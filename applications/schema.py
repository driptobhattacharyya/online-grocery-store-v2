"""Idempotent SQLite schema and demo seed.

Run `python -m applications.schema` to create the database and, when
SEED_DEMO_DATA=1 (the default), load the portfolio catalog.
"""

import os
from datetime import date, timedelta

from applications.database import get_db
from applications.security import hash_password

_ready = set()

SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    email TEXT PRIMARY KEY,
    password TEXT NOT NULL,
    role TEXT NOT NULL DEFAULT 'customer'
);

CREATE TABLE IF NOT EXISTS user_profiles (
    email TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    address TEXT,
    phone TEXT,
    FOREIGN KEY (email) REFERENCES users(email)
);

CREATE TABLE IF NOT EXISTS categories (
    categoryID INTEGER PRIMARY KEY AUTOINCREMENT,
    category_name TEXT NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS products (
    productID INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    manufacture_date TEXT,
    expiry_date TEXT,
    price REAL NOT NULL,
    dynamic_price REAL,
    is_recommended INTEGER DEFAULT 0,
    categoryID INTEGER NOT NULL,
    unit TEXT NOT NULL,
    description TEXT DEFAULT '',
    FOREIGN KEY (categoryID) REFERENCES categories(categoryID)
);

CREATE TABLE IF NOT EXISTS inventory (
    inventoryId INTEGER PRIMARY KEY AUTOINCREMENT,
    productID INTEGER NOT NULL UNIQUE,
    quantity INTEGER NOT NULL DEFAULT 0,
    FOREIGN KEY (productID) REFERENCES products(productID)
);

CREATE TABLE IF NOT EXISTS cart (
    cartID INTEGER PRIMARY KEY AUTOINCREMENT,
    email TEXT NOT NULL,
    product_id INTEGER NOT NULL,
    quantity INTEGER NOT NULL,
    UNIQUE (email, product_id),
    FOREIGN KEY (email) REFERENCES users(email),
    FOREIGN KEY (product_id) REFERENCES products(productID)
);

CREATE TABLE IF NOT EXISTS coupons (
    coupon_code TEXT PRIMARY KEY,
    discount_percentage REAL NOT NULL
);

CREATE TABLE IF NOT EXISTS used_coupons (
    user_email TEXT NOT NULL,
    coupon_code TEXT NOT NULL,
    UNIQUE (user_email, coupon_code),
    FOREIGN KEY (user_email) REFERENCES users(email)
);

CREATE TABLE IF NOT EXISTS cart_coupons (
    email TEXT PRIMARY KEY,
    coupon_code TEXT NOT NULL,
    FOREIGN KEY (email) REFERENCES users(email)
);

CREATE TABLE IF NOT EXISTS orders (
    orderID INTEGER PRIMARY KEY AUTOINCREMENT,
    email TEXT NOT NULL,
    order_date TEXT,
    total_price REAL,
    coupon_code TEXT,
    discount_percentage REAL DEFAULT 0,
    FOREIGN KEY (email) REFERENCES users(email)
);

CREATE TABLE IF NOT EXISTS order_items (
    order_itemID INTEGER PRIMARY KEY AUTOINCREMENT,
    orderID INTEGER NOT NULL,
    product_id INTEGER,
    product_name TEXT NOT NULL,
    quantity INTEGER NOT NULL,
    unit_price REAL,
    FOREIGN KEY (orderID) REFERENCES orders(orderID)
);

CREATE TABLE IF NOT EXISTS store_manager (
    email TEXT PRIMARY KEY,
    manager_status TEXT NOT NULL,
    FOREIGN KEY (email) REFERENCES users(email)
);

CREATE TABLE IF NOT EXISTS reviews (
    reviewID INTEGER PRIMARY KEY AUTOINCREMENT,
    email TEXT NOT NULL,
    product_id INTEGER NOT NULL,
    rating INTEGER NOT NULL,
    body TEXT DEFAULT '',
    created_at TEXT NOT NULL,
    UNIQUE (email, product_id),
    FOREIGN KEY (email) REFERENCES users(email),
    FOREIGN KEY (product_id) REFERENCES products(productID)
);

CREATE TABLE IF NOT EXISTS wishlist (
    email TEXT NOT NULL,
    product_id INTEGER NOT NULL,
    created_at TEXT NOT NULL,
    PRIMARY KEY (email, product_id),
    FOREIGN KEY (email) REFERENCES users(email),
    FOREIGN KEY (product_id) REFERENCES products(productID)
);

CREATE TABLE IF NOT EXISTS app_settings (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL
);
"""

# name, category, price, unit, quantity, description
DEMO_PRODUCTS = [
    ("Apple", "Fruits & Vegetables", 80, "kg", 0, "Fresh red apples sold by the kilogram."),
    ("Banana", "Fruits & Vegetables", 48, "kg", 80, "Ripe bananas, sold by the kilogram."),
    ("Carrot", "Fruits & Vegetables", 40, "kg", 50, "Crunchy carrots for salads and cooking."),
    ("Tomato", "Fruits & Vegetables", 36, "kg", 40, "Juicy tomatoes for curries and salads."),
    ("Onion", "Fruits & Vegetables", 32, "kg", 60, "Everyday cooking onions."),
    ("Pineapple", "Fruits & Vegetables", 60, "piece", 15, "Whole sweet pineapple."),
    ("Strawberry", "Fruits & Vegetables", 90, "box", 6, "A small box of strawberries."),
    ("Milk", "Dairy", 44, "litre", 40, "Fresh dairy milk, one litre."),
    ("Paneer", "Dairy", 90, "pack", 20, "Soft paneer for curries."),
    ("Butter", "Dairy", 55, "pack", 25, "Salted butter for toast and cooking."),
    ("Yogurt", "Dairy", 35, "cup", 30, "Plain yogurt cup."),
    ("Egg", "Poultry", 6, "piece", 200, "Farm eggs, sold per piece."),
    ("Chicken", "Poultry", 220, "kg", 18, "Fresh chicken, sold by the kilogram."),
    ("Bread", "Bakery", 40, "loaf", 24, "Sliced sandwich bread."),
    ("Rice", "Staples", 70, "kg", 50, "Everyday steamed rice."),
    ("Maggi", "Snacks", 30, "packet", 40, "Instant noodles."),
    ("Top Ramen", "Snacks", 35, "packet", 30, "Instant ramen noodles."),
    ("Munch", "Snacks", 20, "packet", 45, "Crunchy chocolate snack."),
    ("Pepsi", "Cold Drinks", 25, "bottle", 40, "Chilled cola bottle."),
    ("Sprite", "Cold Drinks", 20, "bottle", 4, "Lemon-lime cold drink."),
    ("Coffee", "Staples", 120, "pack", 16, "Ground coffee for brewing."),
]


def reset_ready():
    _ready.clear()


def init_schema():
    db = get_db()
    db.executescript(SCHEMA)
    db.execute(
        "INSERT INTO app_settings (key, value) VALUES ('low_stock_threshold', '10') "
        "ON CONFLICT(key) DO NOTHING"
    )
    db.commit()


def ensure_database():
    from applications.database import database_path

    path = database_path()
    if path in _ready:
        return
    init_schema()
    if os.environ.get("SEED_DEMO_DATA", "1") == "1":
        seed_if_empty()
    _ready.add(path)


def create_user(email, password, role, name, phone="", address="", status=None):
    db = get_db()
    db.execute(
        "INSERT INTO users (email, password, role) VALUES (?, ?, ?)",
        (email.lower().strip(), hash_password(password), role),
    )
    db.execute(
        "INSERT INTO user_profiles (email, name, address, phone) VALUES (?, ?, ?, ?)",
        (email.lower().strip(), name, address, phone),
    )
    if role == "manager" or status:
        db.execute(
            "INSERT INTO store_manager (email, manager_status) VALUES (?, ?)",
            (email.lower().strip(), status or "approved"),
        )
    db.commit()


def seed_if_empty():
    db = get_db()
    existing = db.execute("SELECT COUNT(*) AS count FROM users").fetchone()["count"]
    if existing:
        return
    _seed(db)


def _seed(db):
    admin_email = os.environ.get("ADMIN_EMAIL", "admin@grocery.local")
    admin_password = os.environ.get("ADMIN_PASSWORD", "admin123")
    manager_email = os.environ.get("MANAGER_EMAIL", "manager@grocery.local")
    manager_password = os.environ.get("MANAGER_PASSWORD", "manager123")
    customer_email = os.environ.get("CUSTOMER_EMAIL", "customer@grocery.local")
    customer_password = os.environ.get("CUSTOMER_PASSWORD", "customer123")

    accounts = [
        (admin_email, admin_password, "admin", "Store Admin", "9999999999", "Head Office"),
        (manager_email, manager_password, "manager", "Store Manager", "9888888888", "Shop Floor"),
        (customer_email, customer_password, "customer", "Demo Customer", "9777777777", "12 Market Road"),
    ]
    for email, password, role, name, phone, address in accounts:
        db.execute(
            "INSERT INTO users (email, password, role) VALUES (?, ?, ?)",
            (email.lower(), hash_password(password), role),
        )
        db.execute(
            "INSERT INTO user_profiles (email, name, address, phone) VALUES (?, ?, ?, ?)",
            (email.lower(), name, address, phone),
        )
    db.execute(
        "INSERT INTO store_manager (email, manager_status) VALUES (?, 'approved')",
        (manager_email.lower(),),
    )

    category_ids = {}
    for _name, category, *_rest in DEMO_PRODUCTS:
        if category not in category_ids:
            cursor = db.execute("INSERT INTO categories (category_name) VALUES (?)", (category,))
            category_ids[category] = cursor.lastrowid

    today = date.today()
    manufactured = (today - timedelta(days=10)).isoformat()
    expires = (today + timedelta(days=40)).isoformat()
    product_ids = {}
    for name, category, price, unit, quantity, description in DEMO_PRODUCTS:
        cursor = db.execute(
            """
            INSERT INTO products
                (name, manufacture_date, expiry_date, price, unit, categoryID, description)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (name, manufactured, expires, price, unit, category_ids[category], description),
        )
        product_ids[name] = cursor.lastrowid
        db.execute(
            "INSERT INTO inventory (productID, quantity) VALUES (?, ?)",
            (cursor.lastrowid, quantity),
        )

    db.execute(
        "INSERT INTO coupons (coupon_code, discount_percentage) VALUES (?, ?)",
        ("WELCOME10", 10),
    )
    db.execute(
        "INSERT INTO coupons (coupon_code, discount_percentage) VALUES (?, ?)",
        ("SAVE20", 20),
    )

    def add_order(email, item_names, when=None):
        when = when or today.isoformat()
        total = 0
        lines = []
        for item_name in item_names:
            product_id = product_ids[item_name]
            price = next(item[2] for item in DEMO_PRODUCTS if item[0] == item_name)
            quantity = 1
            total += price * quantity
            lines.append((product_id, item_name, quantity, price))
        cursor = db.execute(
            "INSERT INTO orders (email, order_date, total_price, discount_percentage) VALUES (?, ?, ?, 0)",
            (email, when, round(total, 2)),
        )
        order_id = cursor.lastrowid
        for product_id, item_name, quantity, price in lines:
            db.execute(
                """
                INSERT INTO order_items (orderID, product_id, product_name, quantity, unit_price)
                VALUES (?, ?, ?, ?, ?)
                """,
                (order_id, product_id, item_name, quantity, price),
            )

    # Historical baskets that make "frequently bought together" visible.
    shoppers = [
        ("shopper1@example.com", ["Milk", "Bread", "Butter"]),
        ("shopper2@example.com", ["Milk", "Bread"]),
        ("shopper3@example.com", ["Milk", "Egg"]),
        ("shopper4@example.com", ["Chicken", "Onion"]),
        ("shopper5@example.com", ["Chicken", "Onion", "Tomato"]),
        ("shopper6@example.com", ["Maggi", "Egg"]),
        ("shopper7@example.com", ["Banana", "Coffee"]),
        ("shopper8@example.com", ["Pepsi", "Munch"]),
    ]
    for email, items in shoppers:
        db.execute(
            "INSERT INTO users (email, password, role) VALUES (?, ?, 'customer')",
            (email, hash_password("shopper-not-for-login")),
        )
        db.execute(
            "INSERT INTO user_profiles (email, name, address, phone) VALUES (?, ?, '', '')",
            (email, email.split("@")[0]),
        )
        add_order(email, items)

    # The demo customer has purchased milk and bread, so ratings can be tried immediately.
    add_order(customer_email.lower(), ["Milk", "Bread"])
    db.commit()


if __name__ == "__main__":
    from app import app

    with app.app_context():
        ensure_database()
        from applications.database import database_path

        print(f"Database ready at {database_path()}")
