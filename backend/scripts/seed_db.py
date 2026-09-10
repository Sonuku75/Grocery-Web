import asyncio
import os
import sys
from decimal import Decimal

# Ensure backend root is in python path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from app.core.database import AsyncSessionPrimary
from app.core.security import get_password_hash
from app.models.category import Category
from app.models.product import Product
from app.models.user import User

CATEGORIES_DATA = [
    {
        "id": "cat_fruits_veg",
        "slug": "fruits-vegetables",
        "name": "Fruits & Vegetables",
        "description": "Fresh farm-picked fruits and seasonal vegetables.",
        "icon": "Apple",
        "image_url": "https://images.unsplash.com/photo-1610832958506-aa56368176cf?w=400&q=80",
        "sort_order": 1,
    },
    {
        "id": "cat_dairy",
        "slug": "dairy-breakfast",
        "name": "Dairy & Breakfast",
        "description": "Milk, butter, cheese, eggs, and bread.",
        "icon": "Coffee",
        "image_url": "https://images.unsplash.com/photo-1550583724-b2692b85b150?w=400&q=80",
        "sort_order": 2,
    },
    {
        "id": "cat_snacks",
        "slug": "snacks-munchies",
        "name": "Snacks & Munchies",
        "description": "Chips, crisps, namkeen, roasted nuts, and popcorn.",
        "icon": "Cookie",
        "image_url": "https://images.unsplash.com/photo-1566478989037-eec170784d0b?w=400&q=80",
        "sort_order": 3,
    },
    {
        "id": "cat_beverages",
        "slug": "beverages",
        "name": "Beverages",
        "description": "Fruit juices, energy drinks, tea, and premium coffee.",
        "icon": "Wine",
        "image_url": "https://images.unsplash.com/photo-1544145945-f90425340c7e?w=400&q=80",
        "sort_order": 4,
    },
    {
        "id": "cat_bakery",
        "slug": "bakery-biscuits",
        "name": "Bakery & Biscuits",
        "description": "Fresh artisan breads, cookies, cakes, and buns.",
        "icon": "Cake",
        "image_url": "https://images.unsplash.com/photo-1509440159596-0249088772ff?w=400&q=80",
        "sort_order": 5,
    },
    {
        "id": "cat_instant",
        "slug": "instant-food",
        "name": "Instant Food",
        "description": "Noodles, pasta, ready-to-eat meals, and soup mixes.",
        "icon": "UtensilsCrossed",
        "image_url": "https://images.unsplash.com/photo-1612927601601-6638404737ce?w=400&q=80",
        "sort_order": 6,
    },
]

PRODUCTS_DATA = [
    # Fruits & Veg
    {
        "id": "prod_001",
        "slug": "fresh-organic-bananas",
        "name": "Fresh Organic Bananas",
        "brand": "FarmFresh",
        "category_id": "cat_fruits_veg",
        "description": "Naturally ripened sweet bananas packed with potassium and essential nutrients.",
        "specifications": {"Origin": "Maharashtra", "Shelf Life": "3 days", "Organic": "Yes"},
        "price": Decimal("45.00"),
        "original_price": Decimal("60.00"),
        "discount_percent": 25,
        "unit": "1 kg (approx 6-8 pcs)",
        "stock": 5000,
        "rating": Decimal("4.8"),
        "rating_count": 1240,
        "images": ["https://images.unsplash.com/photo-1571771894821-ce9b6c11b08e?w=500&q=80"],
        "tags": ["organic", "fruits", "potassium", "fresh"],
        "is_popular": True,
        "is_featured": True,
        "is_deal": True,
    },
    {
        "id": "prod_002",
        "slug": "shimla-red-apples",
        "name": "Shimla Royal Apples",
        "brand": "Himachal Orchards",
        "category_id": "cat_fruits_veg",
        "description": "Crisp, juicy red apples handpicked from Shimla high-altitude orchards.",
        "specifications": {"Origin": "Himachal Pradesh", "Grade": "A+"},
        "price": Decimal("160.00"),
        "original_price": Decimal("200.00"),
        "discount_percent": 20,
        "unit": "1 kg (4 pcs)",
        "stock": 4200,
        "rating": Decimal("4.9"),
        "rating_count": 890,
        "images": ["https://images.unsplash.com/photo-1560806887-1e4cd0b6cbd6?w=500&q=80"],
        "tags": ["apples", "fruits", "orchard"],
        "is_popular": True,
        "is_featured": True,
        "is_deal": True,
    },
    {
        "id": "prod_003",
        "slug": "hybrid-tomatoes",
        "name": "Farm Fresh Red Tomatoes",
        "brand": "FarmFresh",
        "category_id": "cat_fruits_veg",
        "description": "Plump, ripe tomatoes ideal for rich curries, gravies, and fresh salads.",
        "specifications": {"Type": "Hybrid", "Origin": "Karnataka"},
        "price": Decimal("32.00"),
        "original_price": Decimal("40.00"),
        "discount_percent": 20,
        "unit": "1 kg",
        "stock": 8000,
        "rating": Decimal("4.6"),
        "rating_count": 640,
        "images": ["https://images.unsplash.com/photo-1592924357228-91a4daadcfea?w=500&q=80"],
        "tags": ["vegetables", "curry", "fresh"],
        "is_popular": True,
        "is_featured": False,
        "is_deal": False,
    },
    # Dairy
    {
        "id": "prod_004",
        "slug": "amul-gold-full-cream-milk",
        "name": "Amul Gold Full Cream Milk",
        "brand": "Amul",
        "category_id": "cat_dairy",
        "description": "Pasteurized homogenized full-cream cow and buffalo milk with 6.0% fat minimum.",
        "specifications": {"Fat Content": "6.0%", "SNF": "9.0%"},
        "price": Decimal("33.00"),
        "original_price": Decimal("33.00"),
        "discount_percent": 0,
        "unit": "500 ml pouch",
        "stock": 15000,
        "rating": Decimal("4.9"),
        "rating_count": 3400,
        "images": ["https://images.unsplash.com/photo-1550583724-b2692b85b150?w=500&q=80"],
        "tags": ["milk", "dairy", "breakfast", "amul"],
        "is_popular": True,
        "is_featured": True,
        "is_deal": False,
    },
    {
        "id": "prod_005",
        "slug": "amul-salted-butter-500g",
        "name": "Amul Butter Pasteurized",
        "brand": "Amul",
        "category_id": "cat_dairy",
        "description": "The classic Taste of India butter made from fresh pure milk fat.",
        "specifications": {"Weight": "500g", "Type": "Salted"},
        "price": Decimal("275.00"),
        "original_price": Decimal("290.00"),
        "discount_percent": 5,
        "unit": "500 g pack",
        "stock": 6000,
        "rating": Decimal("4.9"),
        "rating_count": 2100,
        "images": ["https://images.unsplash.com/photo-1589985270826-4b7bb135bc9d?w=500&q=80"],
        "tags": ["butter", "dairy", "baking"],
        "is_popular": True,
        "is_featured": True,
        "is_deal": True,
    },
    # Beverages
    {
        "id": "prod_006",
        "slug": "tata-tea-gold",
        "name": "Tata Tea Gold Leaf & Gently Rolled Long Leaves",
        "brand": "Tata Tea",
        "category_id": "cat_beverages",
        "description": "Exquisite blend of fine Assam tea and gently rolled aromatic long leaves.",
        "specifications": {"Net Weight": "500g", "Form": "Granules & Leaves"},
        "price": Decimal("315.00"),
        "original_price": Decimal("350.00"),
        "discount_percent": 10,
        "unit": "500 g",
        "stock": 3500,
        "rating": Decimal("4.7"),
        "rating_count": 1820,
        "images": ["https://images.unsplash.com/photo-1597481499750-3e6b22637e12?w=500&q=80"],
        "tags": ["tea", "assam", "chai", "beverages"],
        "is_popular": True,
        "is_featured": False,
        "is_deal": True,
    },
    # Snacks
    {
        "id": "prod_007",
        "slug": "lays-classic-salted-chips",
        "name": "Lay's Classic Salted Potato Chips",
        "brand": "Lay's",
        "category_id": "cat_snacks",
        "description": "Thinly sliced golden potatoes seasoned with just the right pinch of salt.",
        "specifications": {"Weight": "90g", "Vegetarian": "Yes"},
        "price": Decimal("40.00"),
        "original_price": Decimal("40.00"),
        "discount_percent": 0,
        "unit": "90 g pouch",
        "stock": 12000,
        "rating": Decimal("4.5"),
        "rating_count": 950,
        "images": ["https://images.unsplash.com/photo-1566478989037-eec170784d0b?w=500&q=80"],
        "tags": ["chips", "snacks", "potatoes"],
        "is_popular": True,
        "is_featured": False,
        "is_deal": False,
    },
    # Instant Food
    {
        "id": "prod_008",
        "slug": "maggi-2-minute-masala-noodles-pack-of-4",
        "name": "Maggi 2-Minute Masala Noodles (Pack of 4)",
        "brand": "Nestle",
        "category_id": "cat_instant",
        "description": "India's favorite noodle with the authentic taste of 10 blended spices.",
        "specifications": {"Servings": "4", "Weight": "280g"},
        "price": Decimal("56.00"),
        "original_price": Decimal("60.00"),
        "discount_percent": 7,
        "unit": "280 g (4 x 70g)",
        "stock": 20000,
        "rating": Decimal("4.8"),
        "rating_count": 8900,
        "images": ["https://images.unsplash.com/photo-1612927601601-6638404737ce?w=500&q=80"],
        "tags": ["maggi", "noodles", "instant", "snack"],
        "is_popular": True,
        "is_featured": True,
        "is_deal": True,
    },
]

# Add dummy products up to prod_050 so locust user IDs prod_001 to prod_050 always resolve
for i in range(9, 51):
    cat = CATEGORIES_DATA[i % len(CATEGORIES_DATA)]
    p_id = f"prod_{i:03d}"
    PRODUCTS_DATA.append({
        "id": p_id,
        "slug": f"cartify-essential-product-{i}",
        "name": f"Cartify Quality Pantry Item #{i}",
        "brand": "Cartify Select",
        "category_id": cat["id"],
        "description": f"Premium quality pantry grocery item carefully inspected and packaged.",
        "specifications": {"Quality": "Premium Grade", "Shelf Life": "6 months"},
        "price": Decimal(str(40 + (i * 7) % 250)),
        "original_price": Decimal(str(50 + (i * 7) % 250)),
        "discount_percent": 10 if (i % 3 == 0) else 0,
        "unit": "500 g",
        "stock": 2000 + i * 50,
        "rating": Decimal("4.7"),
        "rating_count": 100 + i * 5,
        "images": [cat["image_url"]],
        "tags": ["grocery", "essential", cat["slug"]],
        "is_popular": i % 4 == 0,
        "is_featured": i % 5 == 0,
        "is_deal": i % 3 == 0,
    })

async def seed():
    print("Connecting to database for seeding...")
    async with AsyncSessionPrimary() as session:
        # Seed categories
        print(f"Seeding {len(CATEGORIES_DATA)} categories...")
        for cat in CATEGORIES_DATA:
            existing = await session.get(Category, cat["id"])
            if not existing:
                session.add(Category(**cat, is_active=True))

        # Seed demo user
        demo_user_id = "usr_demo_cartify_001"
        existing_user = await session.get(User, demo_user_id)
        if not existing_user:
            print("Seeding demo user: demo@cartify.com / Secret123!")
            session.add(
                User(
                    id=demo_user_id,
                    email="demo@cartify.com",
                    mobile="9876543210",
                    full_name="Cartify Demo Shopper",
                    hashed_password=get_password_hash("Secret123!"),
                    role="customer",
                    is_active=True,
                )
            )

        # Seed products
        print(f"Seeding {len(PRODUCTS_DATA)} products...")
        for p in PRODUCTS_DATA:
            existing_p = await session.get(Product, p["id"])
            if not existing_p:
                session.add(
                    Product(
                        **p,
                        in_stock=p["stock"] > 0,
                        is_active=True,
                    )
                )

        await session.commit()
        print("Seeding completed successfully!")

if __name__ == "__main__":
    asyncio.run(seed())
