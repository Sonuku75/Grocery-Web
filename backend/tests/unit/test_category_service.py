"""
Unit tests for Cartify Category Service (Module 3)
Tests slug generation, hierarchy validation, circular reference prevention, and deactivation rules.
"""

from unittest.mock import AsyncMock, patch
import pytest

from app.core.errors import CartifyException, NotFoundError
from app.models.category import Category
from app.schemas.category import CategoryCreateRequest, CategoryUpdateRequest
from app.services.category import CategoryService, slugify


def test_slugify_formatting():
    assert slugify("Fruits & Vegetables") == "fruits-and-vegetables"
    assert slugify("Dairy & Breakfast") == "dairy-and-breakfast"
    assert slugify("  Fresh   Apples!  ") == "fresh-apples"
    assert slugify("Cold-Pressed 100% Juices") == "cold-pressed-100-juices"
    assert slugify("---Leading and Trailing---") == "leading-and-trailing"


@pytest.mark.asyncio
async def test_generate_unique_slug_no_collision():
    mock_db = AsyncMock()
    with patch("app.repositories.category.CategoryRepository.slug_exists", new=AsyncMock(return_value=False)):
        slug = await CategoryService._generate_unique_slug(mock_db, "Fruits & Vegetables")
        assert slug == "fruits-and-vegetables"


@pytest.mark.asyncio
async def test_generate_unique_slug_with_collisions():
    mock_db = AsyncMock()
    # First call True (taken), second call True (taken), third call False (available)
    with patch(
        "app.repositories.category.CategoryRepository.slug_exists",
        new=AsyncMock(side_effect=[True, True, False]),
    ):
        slug = await CategoryService._generate_unique_slug(mock_db, "Fruits & Vegetables")
        assert slug == "fruits-and-vegetables-3"


@pytest.mark.asyncio
async def test_create_category_with_custom_slug_collision_raises_409():
    mock_db = AsyncMock()
    with patch("app.repositories.category.CategoryRepository.slug_exists", new=AsyncMock(return_value=True)):
        req = CategoryCreateRequest(name="Organic Vegetables", slug="organic-veg")
        with pytest.raises(CartifyException) as exc_info:
            await CategoryService.create_category(mock_db, req)
        assert exc_info.value.status_code == 409
        assert exc_info.value.code == "CATEGORY_SLUG_ALREADY_EXISTS"


@pytest.mark.asyncio
async def test_self_parenting_forbidden():
    mock_db = AsyncMock()
    with pytest.raises(CartifyException) as exc_info:
        await CategoryService._validate_parent_hierarchy(
            mock_db, parent_id="cat-123", category_id="cat-123"
        )
    assert exc_info.value.status_code == 400
    assert exc_info.value.code == "INVALID_PARENT_CATEGORY"


@pytest.mark.asyncio
async def test_parent_must_exist():
    mock_db = AsyncMock()
    with patch("app.repositories.category.CategoryRepository.get_by_id", new=AsyncMock(return_value=None)):
        with pytest.raises(CartifyException) as exc_info:
            await CategoryService._validate_parent_hierarchy(mock_db, parent_id="non-existent")
        assert exc_info.value.status_code == 404
        assert exc_info.value.code == "INVALID_PARENT_CATEGORY"


@pytest.mark.asyncio
async def test_multi_level_nesting_forbidden():
    mock_db = AsyncMock()
    # Parent already has a parent_id (is a subcategory)
    parent_cat = Category(id="sub-1", name="Apples", slug="apples", parent_id="top-fruits")
    with patch(
        "app.repositories.category.CategoryRepository.get_by_id",
        new=AsyncMock(return_value=parent_cat),
    ):
        with pytest.raises(CartifyException) as exc_info:
            await CategoryService._validate_parent_hierarchy(mock_db, parent_id="sub-1")
        assert exc_info.value.status_code == 400
        assert exc_info.value.code == "INVALID_PARENT_CATEGORY"


@pytest.mark.asyncio
async def test_circular_hierarchy_forbidden():
    mock_db = AsyncMock()
    # Attempting to set parent of cat_A to cat_B, but cat_B has parent cat_A
    cat_b = Category(id="cat-b", name="Category B", slug="cat-b", parent_id="cat-a")
    with patch(
        "app.repositories.category.CategoryRepository.get_by_id",
        new=AsyncMock(return_value=cat_b),
    ):
        with pytest.raises(CartifyException) as exc_info:
            await CategoryService._validate_parent_hierarchy(
                mock_db, parent_id="cat-b", category_id="cat-a"
            )
        assert exc_info.value.status_code == 400
        assert exc_info.value.code == "CATEGORY_CIRCULAR_REFERENCE"


@pytest.mark.asyncio
async def test_hard_delete_rejected_with_active_children():
    mock_db = AsyncMock()
    cat = Category(id="top-fruits", name="Fruits", slug="fruits", parent_id=None)
    with patch(
        "app.repositories.category.CategoryRepository.get_by_id",
        new=AsyncMock(return_value=cat),
    ), patch(
        "app.repositories.category.CategoryRepository.count_children",
        new=AsyncMock(return_value=3),
    ):
        with pytest.raises(CartifyException) as exc_info:
            await CategoryService.delete_category(mock_db, "top-fruits", hard_delete=True)
        assert exc_info.value.status_code == 400
        assert exc_info.value.code == "CATEGORY_HAS_DEPENDENCIES"


@pytest.mark.asyncio
async def test_soft_deactivation_cascades_to_children():
    mock_db = AsyncMock()
    cat = Category(id="top-fruits", name="Fruits", slug="fruits", parent_id=None, is_active=True)
    child1 = Category(id="sub-1", name="Apples", slug="apples", parent_id="top-fruits", is_active=True)
    child2 = Category(id="sub-2", name="Berries", slug="berries", parent_id="top-fruits", is_active=True)

    with patch(
        "app.repositories.category.CategoryRepository.get_by_id",
        new=AsyncMock(return_value=cat),
    ), patch(
        "app.repositories.category.CategoryRepository.list_subcategories",
        new=AsyncMock(return_value=[child1, child2]),
    ), patch(
        "app.repositories.category.CategoryRepository.update",
        new=AsyncMock(),
    ) as mock_update, patch(
        "app.core.redis.CacheManager.delete_pattern",
        new=AsyncMock(),
    ):
        res = await CategoryService.delete_category(mock_db, "top-fruits", hard_delete=False)
        assert "deactivated successfully" in res["message"]
        # Update called for parent and each child (3 times)
        assert mock_update.call_count == 3
