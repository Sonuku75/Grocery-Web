import random
import uuid
from locust import HttpUser, task, between, events
import logging

logger = logging.getLogger("cartify.locust")

# Sample product and category IDs matching seed data
PRODUCT_IDS = [f"prod_{i:03d}" for i in range(1, 51)]
CATEGORIES = [
    "fruits-vegetables",
    "dairy-breakfast",
    "snacks-munchies",
    "beverages",
    "bakery-biscuits",
    "instant-food",
]

class CartifyShopperUser(HttpUser):
    """
    Simulates standard shopper browsing patterns (85% read traffic).
    Tests Redis Cache-Aside, Keyset Pagination, and PostgreSQL Read Replica offload.
    """
    weight = 85
    wait_time = between(0.5, 2.0)

    @task(4)
    def browse_homepage(self):
        with self.client.get("/api/v1/categories", name="Categories - List", catch_response=True) as resp:
            if resp.status_code != 200:
                resp.failure(f"Failed to fetch categories: {resp.status_code}")

        with self.client.get("/api/v1/products?limit=12", name="Products - Home Feed", catch_response=True) as resp:
            if resp.status_code != 200:
                resp.failure(f"Failed to fetch homepage products: {resp.status_code}")

    @task(3)
    def filter_by_category(self):
        cat = random.choice(CATEGORIES)
        with self.client.get(
            f"/api/v1/products?category={cat}&limit=12",
            name="Products - Filter by Category",
            catch_response=True,
        ) as resp:
            if resp.status_code != 200:
                resp.failure(f"Category filter failed: {resp.status_code}")

    @task(2)
    def search_products(self):
        query = random.choice(["milk", "apple", "bread", "tea", "coffee", "rice"])
        with self.client.get(
            f"/api/v1/products?search={query}&limit=12",
            name="Products - Search Keyset",
            catch_response=True,
        ) as resp:
            if resp.status_code != 200:
                resp.failure(f"Search failed: {resp.status_code}")

    @task(3)
    def view_product_detail(self):
        pid = random.choice(PRODUCT_IDS)
        with self.client.get(
            f"/api/v1/products/{pid}",
            name="Products - View Detail (Cache-Aside)",
            catch_response=True,
        ) as resp:
            if resp.status_code not in (200, 404):
                resp.failure(f"Product detail query error: {resp.status_code}")

class CartifyCheckoutUser(HttpUser):
    """
    Simulates transactional checkout (15% write traffic).
    Tests:
    1. Row-level locks and deadlock prevention under concurrent stock updates.
    2. Redis distributed idempotency locks.
    3. PgBouncer transaction-level connection handling.
    """
    weight = 15
    wait_time = between(1.0, 3.0)

    def on_start(self):
        """Register / login test user for the checkout session."""
        user_num = random.randint(1000, 999999)
        self.email = f"user_{user_num}_{uuid.uuid4().hex[:6]}@cartify.test"
        self.token = None

        resp = self.client.post(
            "/api/v1/auth/register",
            json={
                "full_name": f"Test User {user_num}",
                "email": self.email,
                "mobile": f"9{random.randint(100000000, 999999999)}",
                "password": "SecurePassword123!",
            },
            name="Auth - Register",
        )
        if resp.status_code == 201:
            data = resp.json().get("data", {})
            self.token = data.get("access_token")

    @task(2)
    def add_to_cart_and_view(self):
        if not self.token:
            return
        headers = {"Authorization": f"Bearer {self.token}"}
        pid = random.choice(PRODUCT_IDS)

        # Add item
        self.client.post(
            "/api/v1/cart/items",
            json={"product_id": pid, "quantity": 1},
            headers=headers,
            name="Cart - Add Item",
        )
        # Fetch cart
        self.client.get(
            "/api/v1/cart",
            headers=headers,
            name="Cart - Fetch Summary",
        )

    @task(1)
    def place_order_with_idempotency(self):
        if not self.token:
            return

        headers = {
            "Authorization": f"Bearer {self.token}",
            "Idempotency-Key": f"locust_order_{uuid.uuid4()}",
        }

        # Multi-item checkout to stress row-locking and deadlock safety
        sample_pids = random.sample(PRODUCT_IDS, k=min(3, len(PRODUCT_IDS)))
        order_payload = {
            "items": [{"product_id": pid, "quantity": random.randint(1, 2)} for pid in sample_pids],
            "delivery_address": {
                "street": "123 Tech Park Blvd",
                "city": "Bengaluru",
                "state": "Karnataka",
                "postal_code": "560100",
            },
            "delivery_slot": "15 Minutes Express",
            "payment_method": "card",
            "coupon_code": "WELCOME50" if random.random() > 0.5 else None,
        }

        with self.client.post(
            "/api/v1/orders",
            json=order_payload,
            headers=headers,
            name="Orders - Create Checkout (Atomic Lock)",
            catch_response=True,
        ) as resp:
            # 201 Created or 409 Conflict (insufficient stock under heavy load) are expected valid responses
            if resp.status_code in (201, 409):
                resp.success()
            else:
                resp.failure(f"Unexpected checkout response: {resp.status_code} - {resp.text}")

        # Test Idempotency Retry: repeat exact same request with same key
        with self.client.post(
            "/api/v1/orders",
            json=order_payload,
            headers=headers,
            name="Orders - Idempotent Retry",
            catch_response=True,
        ) as retry_resp:
            if retry_resp.status_code in (200, 201, 409):
                retry_resp.success()
            else:
                retry_resp.failure(f"Idempotency retry failed: {retry_resp.status_code}")
