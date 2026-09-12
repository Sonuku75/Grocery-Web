"""004_products_tables

Revision ID: 004_products_tables
Revises: 003_categories_table
Create Date: 2026-09-11 23:20:00.000000

Module 4: Product Catalog & Product Variants
Creates products, product_variants, and product_images tables with:
- Check constraints enforcing price >= 0, mrp >= 0, price <= mrp
- Foreign keys with ON DELETE RESTRICT on category and ON DELETE CASCADE on variants/images
- Keyset pagination composite indexes for ultra-fast query performance
- Strict uppercase unique SKU constraint
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = "004_products_tables"
down_revision: Union[str, None] = "003_categories_table"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. products table
    op.create_table(
        "products",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column(
            "category_id",
            sa.String(36),
            sa.ForeignKey("categories.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("slug", sa.String(255), nullable=False),
        sa.Column("brand", sa.String(128), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("short_description", sa.String(500), nullable=True),
        sa.Column("image_url", sa.String(1024), nullable=True),
        sa.Column("is_active", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        sa.Column("is_featured", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )
    op.create_index("ix_products_slug", "products", ["slug"], unique=True)
    op.create_index("ix_products_category_id", "products", ["category_id"])
    op.create_index("ix_products_brand", "products", ["brand"])
    op.create_index("ix_products_is_active", "products", ["is_active"])
    op.create_index("ix_products_is_featured", "products", ["is_featured"])
    op.create_index("idx_products_cat_active_featured", "products", ["category_id", "is_active", "is_featured"])
    op.create_index("idx_products_brand_active", "products", ["brand", "is_active"])
    op.create_index("idx_products_keyset", "products", ["is_active", "created_at", "id"])

    # 2. product_variants table
    op.create_table(
        "product_variants",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column(
            "product_id",
            sa.String(36),
            sa.ForeignKey("products.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("sku", sa.String(64), nullable=False),
        sa.Column("name", sa.String(128), nullable=False),
        sa.Column("unit_value", sa.Numeric(10, 2), nullable=False),
        sa.Column("unit_type", sa.String(32), nullable=False),
        sa.Column("price", sa.Numeric(10, 2), nullable=False),
        sa.Column("mrp", sa.Numeric(10, 2), nullable=False),
        sa.Column("discount_percentage", sa.Integer(), server_default=sa.text("0"), nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        sa.Column("sort_order", sa.Integer(), server_default=sa.text("0"), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.CheckConstraint("price >= 0", name="chk_variant_price_non_negative"),
        sa.CheckConstraint("mrp >= 0", name="chk_variant_mrp_non_negative"),
        sa.CheckConstraint("price <= mrp", name="chk_variant_price_le_mrp"),
    )
    op.create_index("ix_product_variants_sku", "product_variants", ["sku"], unique=True)
    op.create_index("ix_product_variants_product_id", "product_variants", ["product_id"])
    op.create_index("ix_product_variants_is_active", "product_variants", ["is_active"])
    op.create_index("idx_variants_prod_active_sort", "product_variants", ["product_id", "is_active", "sort_order"])

    # 3. product_images table
    op.create_table(
        "product_images",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column(
            "product_id",
            sa.String(36),
            sa.ForeignKey("products.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("image_url", sa.String(1024), nullable=False),
        sa.Column("alt_text", sa.String(255), nullable=True),
        sa.Column("sort_order", sa.Integer(), server_default=sa.text("0"), nullable=False),
        sa.Column("is_primary", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )
    op.create_index("ix_product_images_product_id", "product_images", ["product_id"])
    op.create_index("ix_product_images_is_primary", "product_images", ["is_primary"])
    op.create_index("idx_prod_images_prod_sort", "product_images", ["product_id", "sort_order"])
    op.create_index("idx_prod_images_prod_primary", "product_images", ["product_id", "is_primary"])


def downgrade() -> None:
    op.drop_table("product_images")
    op.drop_table("product_variants")
    op.drop_table("products")
