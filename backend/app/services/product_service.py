"""
Cartify Product Service (Module 4)

Domain business logic for products, variants, and gallery images:
- Authoritative INR pricing (price, mrp, and discount calculation)
- Strict single primary image invariant and automatic product thumbnail synchronization
- Uppercase unique SKU enforcement
- Safe URL slug generation with collision resolution
- Keyset cursor pagination and whitelisted sorting
- Redis cache-aside with automated invalidation
- Mass assignment protection
"""

import logging
import re
from decimal import Decimal
from typing import Any, Dict, List, Optional
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.errors import CartifyException, NotFoundError
from app.core.redis import CacheManager
from app.models.category import Category
from app.models.product import Product
from app.models.product_image import ProductImage
from app.models.product_variant import ProductVariant
from app.repositories.category import CategoryRepository
from app.repositories.product import ProductRepository
from app.repositories.product_image import ProductImageRepository
from app.repositories.product_variant import ProductVariantRepository
from app.schemas.category import CategoryResponse
from app.schemas.product import (
    ProductCreate,
    ProductDetailResponse,
    ProductFilterParams,
    ProductListResponse,
    ProductSummaryResponse,
    ProductUpdate,
)
from app.schemas.product_image import ProductImageCreate, ProductImageResponse, ProductImageUpdate
from app.schemas.product_variant import (
    ProductVariantCreate,
    ProductVariantResponse,
    ProductVariantUpdate,
)

logger = logging.getLogger("cartify.products")


def slugify(text: str) -> str:
    """Converts display text into a clean URL-safe slug."""
    text = text.replace("&", "and")
    text = text.lower()
    text = re.sub(r"[^a-z0-9]+", "-", text)
    slug = text.strip("-")
    return slug or "product"


def calculate_discount_percentage(price: Decimal, mrp: Decimal) -> int:
    """Computes authoritative discount percentage based on selling price and MRP."""
    if mrp <= 0 or price >= mrp:
        return 0
    discount = ((mrp - price) / mrp) * Decimal(100)
    return int(round(discount))


class ProductService:
    CACHE_KEY_PREFIX = "cache:products:"
    CACHE_TTL_SECONDS = 300  # 5 minutes

    @classmethod
    async def _invalidate_product_cache(cls, product_id: str, slug: Optional[str] = None) -> None:
        """Invalidates product-specific and general catalog cached entries."""
        try:
            keys = [
                f"{cls.CACHE_KEY_PREFIX}id:{product_id}",
                f"{cls.CACHE_KEY_PREFIX}list:*",
            ]
            if slug:
                keys.append(f"{cls.CACHE_KEY_PREFIX}slug:{slug}")
            for k in keys:
                await CacheManager.delete_pattern(k)
        except Exception as e:
            logger.warning(f"Failed to invalidate product cache: {e}")

    @classmethod
    async def ensure_unique_slug(
        cls,
        db: AsyncSession,
        base_name: str,
        exclude_id: Optional[str] = None,
    ) -> str:
        """Generates a URL-safe slug, disambiguating collisions with numeric suffixes."""
        base_slug = slugify(base_name)
        candidate = base_slug
        counter = 2
        while await ProductRepository.slug_exists(db, candidate, exclude_id):
            candidate = f"{base_slug}-{counter}"
            counter += 1
        return candidate

    @classmethod
    def _format_product_summary(
        cls,
        product: Product,
        active_variants_only: bool = True,
    ) -> ProductSummaryResponse:
        """Transforms a Product ORM instance into a ProductSummaryResponse with calculated aggregates."""
        all_variants = product.variants or []
        variants = [v for v in all_variants if (not active_variants_only or v.is_active)]
        
        min_price = None
        max_price = None
        min_mrp = None
        max_discount = 0
        primary_variant = None

        if variants:
            sorted_by_price = sorted(variants, key=lambda v: (v.price, v.sort_order))
            min_price = sorted_by_price[0].price
            max_price = sorted_by_price[-1].price
            min_mrp = sorted_by_price[0].mrp
            max_discount = max((v.discount_percentage for v in variants), default=0)
            primary_variant = ProductVariantResponse.model_validate(sorted_by_price[0])

        images = product.images or []
        sorted_images = sorted(images, key=lambda img: (not img.is_primary, img.sort_order))

        return ProductSummaryResponse(
            id=product.id,
            category_id=product.category_id,
            category_name=product.category.name if product.category else None,
            category_slug=product.category.slug if product.category else None,
            name=product.name,
            slug=product.slug,
            brand=product.brand,
            description=product.description,
            short_description=product.short_description,
            image_url=product.image_url,
            is_active=product.is_active,
            is_featured=product.is_featured,
            min_price=min_price,
            max_price=max_price,
            min_mrp=min_mrp,
            max_discount_percentage=max_discount,
            primary_variant=primary_variant,
            variants=[ProductVariantResponse.model_validate(v) for v in variants],
            images=[ProductImageResponse.model_validate(img) for img in sorted_images],
            created_at=product.created_at,
            updated_at=product.updated_at,
        )

    @classmethod
    def _format_product_detail(
        cls,
        product: Product,
        active_variants_only: bool = True,
    ) -> ProductDetailResponse:
        """Transforms a Product ORM instance into a full ProductDetailResponse."""
        summary = cls._format_product_summary(product, active_variants_only=active_variants_only)
        category_resp = CategoryResponse.model_validate(product.category) if product.category else None
        return ProductDetailResponse(
            **summary.model_dump(),
            category=category_resp,
        )

    # -------------------------------------------------------------------------
    # Public Customer Methods
    # -------------------------------------------------------------------------

    @classmethod
    async def list_products(
        cls,
        db: AsyncSession,
        filters: ProductFilterParams,
        active_only: bool = True,
    ) -> ProductListResponse:
        """Lists products matching filter criteria with keyset cursor pagination."""
        is_feat = filters.is_featured if filters.is_featured is not None else filters.featured

        items, next_cursor, has_more, total = await ProductRepository.list_products(
            db=db,
            active_only=active_only,
            category_id=filters.category_id,
            subcategory_id=filters.subcategory_id,
            brand=filters.brand,
            is_featured=is_feat,
            sort=filters.sort or "newest",
            limit=filters.limit,
            cursor=filters.cursor,
        )

        formatted_items = [
            cls._format_product_summary(p, active_variants_only=active_only)
            for p in items
        ]

        return ProductListResponse(
            items=formatted_items,
            next_cursor=next_cursor,
            has_more=has_more,
            total=total,
        )

    @classmethod
    async def get_by_id(
        cls,
        db: AsyncSession,
        product_id: str,
        active_only: bool = True,
    ) -> ProductDetailResponse:
        """Retrieves a single product detail by ID with Redis cache-aside."""
        cache_key = f"{cls.CACHE_KEY_PREFIX}id:{product_id}"
        if active_only:
            cached = await CacheManager.get(cache_key)
            if cached:
                try:
                    return ProductDetailResponse.model_validate(cached)
                except Exception:
                    pass

        product = await ProductRepository.get_by_id(db, product_id, active_only=active_only)
        if not product:
            raise NotFoundError("Product", product_id)

        response = cls._format_product_detail(product, active_variants_only=active_only)
        if active_only:
            try:
                await CacheManager.set(cache_key, response.model_dump(mode="json"), ttl_seconds=cls.CACHE_TTL_SECONDS)
            except Exception:
                pass

        return response

    @classmethod
    async def get_by_slug(
        cls,
        db: AsyncSession,
        slug: str,
        active_only: bool = True,
    ) -> ProductDetailResponse:
        """Retrieves a single product detail by unique URL slug with Redis cache-aside."""
        cache_key = f"{cls.CACHE_KEY_PREFIX}slug:{slug}"
        if active_only:
            cached = await CacheManager.get(cache_key)
            if cached:
                try:
                    return ProductDetailResponse.model_validate(cached)
                except Exception:
                    pass

        product = await ProductRepository.get_by_slug(db, slug, active_only=active_only)
        if not product:
            raise NotFoundError("Product", slug)

        response = cls._format_product_detail(product, active_variants_only=active_only)
        if active_only:
            try:
                await CacheManager.set(cache_key, response.model_dump(mode="json"), ttl_seconds=cls.CACHE_TTL_SECONDS)
            except Exception:
                pass

        return response

    # -------------------------------------------------------------------------
    # Admin Product Management Methods
    # -------------------------------------------------------------------------

    @classmethod
    async def create_product(
        cls,
        db: AsyncSession,
        data: ProductCreate,
    ) -> ProductDetailResponse:
        """Creates product, initial variants, and images transactionally."""
        # 1. Validate category exists
        category = await CategoryRepository.get_by_id(db, data.category_id, active_only=False)
        if not category:
            raise CartifyException(
                status_code=400,
                message=f"Category with ID '{data.category_id}' does not exist.",
                code="INVALID_CATEGORY",
            )

        # 2. Generate unique slug
        slug = await cls.ensure_unique_slug(db, data.name)

        # 3. Validate initial variant SKUs if provided
        for v in data.variants:
            if await ProductVariantRepository.sku_exists(db, v.sku):
                raise CartifyException(
                    status_code=409,
                    message=f"Product variant with SKU '{v.sku}' already exists.",
                    code="DUPLICATE_SKU",
                )

        # 4. Create Product record
        product_dict = {
            "category_id": data.category_id,
            "name": data.name,
            "slug": slug,
            "brand": data.brand,
            "description": data.description,
            "short_description": data.short_description,
            "image_url": data.image_url,
            "is_active": data.is_active,
            "is_featured": data.is_featured,
        }
        product = await ProductRepository.create(db, product_dict)

        # 5. Create initial variants
        for v in data.variants:
            discount = calculate_discount_percentage(v.price, v.mrp)
            v_dict = {
                "product_id": product.id,
                "sku": v.sku,
                "name": v.name,
                "unit_value": v.unit_value,
                "unit_type": v.unit_type,
                "price": v.price,
                "mrp": v.mrp,
                "discount_percentage": discount,
                "sort_order": v.sort_order,
                "is_active": v.is_active,
            }
            await ProductVariantRepository.create(db, v_dict)

        # 6. Create initial images
        primary_url = data.image_url
        for idx, img in enumerate(data.images):
            is_prim = img.is_primary or (idx == 0 and not primary_url)
            img_dict = {
                "product_id": product.id,
                "image_url": img.image_url,
                "alt_text": img.alt_text,
                "sort_order": img.sort_order,
                "is_primary": is_prim,
            }
            await ProductImageRepository.create(db, img_dict)
            if is_prim and not product.image_url:
                await ProductRepository.update(db, product, {"image_url": img.image_url})

        await cls._invalidate_product_cache(product.id, slug=product.slug)
        # Fetch fresh product with relationships
        refreshed = await ProductRepository.get_by_id(db, product.id, active_only=False)
        return cls._format_product_detail(refreshed, active_variants_only=False)

    @classmethod
    async def update_product(
        cls,
        db: AsyncSession,
        product_id: str,
        data: ProductUpdate,
    ) -> ProductDetailResponse:
        """Updates product metadata with mass assignment protection."""
        product = await ProductRepository.get_by_id(db, product_id, active_only=False)
        if not product:
            raise NotFoundError("Product", product_id)

        update_dict: Dict[str, Any] = {}
        dumped = data.model_dump(exclude_unset=True)

        # Validate category if changed
        if "category_id" in dumped:
            new_cat = await CategoryRepository.get_by_id(db, dumped["category_id"], active_only=False)
            if not new_cat:
                raise CartifyException(
                    status_code=400,
                    message=f"Category with ID '{dumped['category_id']}' does not exist.",
                    code="INVALID_CATEGORY",
                )
            update_dict["category_id"] = dumped["category_id"]

        # Regenerate slug if title changed
        if "name" in dumped and dumped["name"] != product.name:
            update_dict["name"] = dumped["name"]
            update_dict["slug"] = await cls.ensure_unique_slug(db, dumped["name"], exclude_id=product.id)

        for field in ("brand", "description", "short_description", "image_url", "is_featured", "is_active"):
            if field in dumped:
                update_dict[field] = dumped[field]

        old_slug = product.slug
        if update_dict:
            await ProductRepository.update(db, product, update_dict)

        await cls._invalidate_product_cache(product.id, slug=old_slug)
        if product.slug != old_slug:
            await cls._invalidate_product_cache(product.id, slug=product.slug)

        refreshed = await ProductRepository.get_by_id(db, product_id, active_only=False)
        return cls._format_product_detail(refreshed, active_variants_only=False)

    @classmethod
    async def update_product_status(
        cls,
        db: AsyncSession,
        product_id: str,
        is_active: bool,
    ) -> ProductDetailResponse:
        """Toggles active/inactive customer visibility status."""
        product = await ProductRepository.get_by_id(db, product_id, active_only=False)
        if not product:
            raise NotFoundError("Product", product_id)

        await ProductRepository.update(db, product, {"is_active": is_active})
        await cls._invalidate_product_cache(product.id, slug=product.slug)

        refreshed = await ProductRepository.get_by_id(db, product_id, active_only=False)
        return cls._format_product_detail(refreshed, active_variants_only=False)

    # -------------------------------------------------------------------------
    # Admin Product Variant Methods
    # -------------------------------------------------------------------------

    @classmethod
    async def create_variant(
        cls,
        db: AsyncSession,
        product_id: str,
        data: ProductVariantCreate,
    ) -> ProductVariantResponse:
        """Adds a variant to an existing product."""
        product = await ProductRepository.get_by_id(db, product_id, active_only=False)
        if not product:
            raise NotFoundError("Product", product_id)

        if await ProductVariantRepository.sku_exists(db, data.sku):
            raise CartifyException(
                status_code=409,
                message=f"Product variant with SKU '{data.sku}' already exists.",
                code="DUPLICATE_SKU",
            )

        if data.price > data.mrp:
            raise CartifyException(
                status_code=422,
                message=f"Selling price ({data.price}) cannot exceed MRP ({data.mrp}).",
                code="INVALID_PRICE",
            )

        discount = calculate_discount_percentage(data.price, data.mrp)
        variant_dict = {
            "product_id": product_id,
            "sku": data.sku,
            "name": data.name,
            "unit_value": data.unit_value,
            "unit_type": data.unit_type,
            "price": data.price,
            "mrp": data.mrp,
            "discount_percentage": discount,
            "sort_order": data.sort_order,
            "is_active": data.is_active,
        }
        variant = await ProductVariantRepository.create(db, variant_dict)
        await cls._invalidate_product_cache(product_id, slug=product.slug)
        return ProductVariantResponse.model_validate(variant)

    @classmethod
    async def update_variant(
        cls,
        db: AsyncSession,
        product_id: str,
        variant_id: str,
        data: ProductVariantUpdate,
    ) -> ProductVariantResponse:
        """Updates variant pricing, unit, SKU, or sorting."""
        variant = await ProductVariantRepository.get_by_id(db, variant_id)
        if not variant or variant.product_id != product_id:
            raise NotFoundError("ProductVariant", variant_id)

        dumped = data.model_dump(exclude_unset=True)
        if "sku" in dumped and dumped["sku"] != variant.sku:
            if await ProductVariantRepository.sku_exists(db, dumped["sku"], exclude_id=variant_id):
                raise CartifyException(
                    status_code=409,
                    message=f"Product variant with SKU '{dumped['sku']}' already exists.",
                    code="DUPLICATE_SKU",
                )

        new_price = dumped.get("price", variant.price)
        new_mrp = dumped.get("mrp", variant.mrp)
        if new_price > new_mrp:
            raise CartifyException(
                status_code=422,
                message=f"Selling price ({new_price}) cannot exceed MRP ({new_mrp}).",
                code="INVALID_PRICE",
            )

        dumped["discount_percentage"] = calculate_discount_percentage(new_price, new_mrp)
        updated = await ProductVariantRepository.update(db, variant, dumped)
        await cls._invalidate_product_cache(product_id)
        return ProductVariantResponse.model_validate(updated)

    @classmethod
    async def update_variant_status(
        cls,
        db: AsyncSession,
        product_id: str,
        variant_id: str,
        is_active: bool,
    ) -> ProductVariantResponse:
        """Toggles active state of an individual variant."""
        variant = await ProductVariantRepository.get_by_id(db, variant_id)
        if not variant or variant.product_id != product_id:
            raise NotFoundError("ProductVariant", variant_id)

        updated = await ProductVariantRepository.update(db, variant, {"is_active": is_active})
        await cls._invalidate_product_cache(product_id)
        return ProductVariantResponse.model_validate(updated)

    # -------------------------------------------------------------------------
    # Admin Product Image Methods
    # -------------------------------------------------------------------------

    @classmethod
    async def add_image(
        cls,
        db: AsyncSession,
        product_id: str,
        data: ProductImageCreate,
    ) -> ProductImageResponse:
        """Adds a gallery image and maintains single primary image invariant."""
        product = await ProductRepository.get_by_id(db, product_id, active_only=False)
        if not product:
            raise NotFoundError("Product", product_id)

        if data.is_primary:
            await ProductImageRepository.clear_primary_for_product(db, product_id)
            await ProductRepository.update(db, product, {"image_url": data.image_url})

        img_dict = {
            "product_id": product_id,
            "image_url": data.image_url,
            "alt_text": data.alt_text,
            "sort_order": data.sort_order,
            "is_primary": data.is_primary,
        }
        image = await ProductImageRepository.create(db, img_dict)
        await cls._invalidate_product_cache(product_id, slug=product.slug)
        return ProductImageResponse.model_validate(image)

    @classmethod
    async def update_image(
        cls,
        db: AsyncSession,
        product_id: str,
        image_id: str,
        data: ProductImageUpdate,
    ) -> ProductImageResponse:
        """Updates image metadata and synchronizes primary image."""
        product = await ProductRepository.get_by_id(db, product_id, active_only=False)
        if not product:
            raise NotFoundError("Product", product_id)

        image = await ProductImageRepository.get_by_id(db, image_id)
        if not image or image.product_id != product_id:
            raise NotFoundError("ProductImage", image_id)

        dumped = data.model_dump(exclude_unset=True)
        if dumped.get("is_primary") is True:
            await ProductImageRepository.clear_primary_for_product(db, product_id)
            target_url = dumped.get("image_url") or image.image_url
            await ProductRepository.update(db, product, {"image_url": target_url})

        updated = await ProductImageRepository.update(db, image, dumped)
        await cls._invalidate_product_cache(product_id, slug=product.slug)
        return ProductImageResponse.model_validate(updated)

    @classmethod
    async def set_primary_image(
        cls,
        db: AsyncSession,
        product_id: str,
        image_id: str,
    ) -> ProductImageResponse:
        """Atomically promotes an image to be the sole primary image for the product."""
        product = await ProductRepository.get_by_id(db, product_id, active_only=False)
        if not product:
            raise NotFoundError("Product", product_id)

        image = await ProductImageRepository.get_by_id(db, image_id)
        if not image or image.product_id != product_id:
            raise NotFoundError("ProductImage", image_id)

        await ProductImageRepository.clear_primary_for_product(db, product_id)
        updated = await ProductImageRepository.update(db, image, {"is_primary": True})
        await ProductRepository.update(db, product, {"image_url": image.image_url})
        await cls._invalidate_product_cache(product_id, slug=product.slug)
        return ProductImageResponse.model_validate(updated)

    @classmethod
    async def delete_image(
        cls,
        db: AsyncSession,
        product_id: str,
        image_id: str,
    ) -> None:
        """Removes an image; if it was primary, reassigns primary to remaining image or clears."""
        product = await ProductRepository.get_by_id(db, product_id, active_only=False)
        if not product:
            raise NotFoundError("Product", product_id)

        image = await ProductImageRepository.get_by_id(db, image_id)
        if not image or image.product_id != product_id:
            raise NotFoundError("ProductImage", image_id)

        was_primary = image.is_primary
        await ProductImageRepository.delete(db, image)

        if was_primary:
            remaining = await ProductImageRepository.list_by_product_id(db, product_id)
            if remaining:
                await ProductImageRepository.update(db, remaining[0], {"is_primary": True})
                await ProductRepository.update(db, product, {"image_url": remaining[0].image_url})
            else:
                await ProductRepository.update(db, product, {"image_url": None})

        await cls._invalidate_product_cache(product_id, slug=product.slug)
