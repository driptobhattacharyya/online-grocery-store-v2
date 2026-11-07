import logging
import os
import secrets
import sqlite3
import time
from datetime import date, timedelta

from flask import g, current_app
from werkzeug.security import generate_password_hash

SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    email    TEXT NOT NULL UNIQUE PRIMARY KEY,
    password TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS user_profiles (
    email   TEXT NOT NULL PRIMARY KEY REFERENCES users(email),
    name    TEXT NOT NULL,
    address TEXT,
    phone   TEXT
);
CREATE TABLE IF NOT EXISTS managers (
    email    TEXT NOT NULL PRIMARY KEY,
    password TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS store_manager (
    email          TEXT PRIMARY KEY,
    manager_status TEXT
);
CREATE TABLE IF NOT EXISTS categories (
    categoryID    INTEGER PRIMARY KEY AUTOINCREMENT,
    category_name TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS products (
    productID        INTEGER PRIMARY KEY AUTOINCREMENT,
    name             TEXT NOT NULL,
    manufacture_date TEXT NOT NULL,
    expiry_date      TEXT NOT NULL,
    price            REAL NOT NULL,
    dynamic_price    REAL,
    is_recommended   INTEGER,
    categoryID       INTEGER NOT NULL,
    unit             TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS inventory (
    inventoryId INTEGER PRIMARY KEY AUTOINCREMENT,
    productID   INTEGER NOT NULL UNIQUE REFERENCES products(productID),
    quantity    INTEGER
);
CREATE TABLE IF NOT EXISTS cart (
    cartID      INTEGER PRIMARY KEY AUTOINCREMENT,
    email       TEXT NOT NULL REFERENCES users(email),
    product_id  INTEGER NOT NULL REFERENCES products(productID),
    quantity    INTEGER NOT NULL,
    isPurchased INTEGER DEFAULT 1
);
CREATE TABLE IF NOT EXISTS coupons (
    coupon_code         TEXT NOT NULL UNIQUE PRIMARY KEY,
    discount_percentage REAL NOT NULL
);
CREATE TABLE IF NOT EXISTS used_coupons (
    user_email  TEXT NOT NULL REFERENCES users(email),
    coupon_code TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS orders (
    orderID     INTEGER PRIMARY KEY AUTOINCREMENT,
    email       TEXT NOT NULL REFERENCES users(email),
    order_date  TEXT,
    total_price NUMERIC
);
CREATE TABLE IF NOT EXISTS order_items (
    order_itemID INTEGER PRIMARY KEY AUTOINCREMENT,
    orderID      INTEGER NOT NULL REFERENCES orders(orderID),
    product_name TEXT NOT NULL,
    quantity     INTEGER
);
CREATE TABLE IF NOT EXISTS meta (
    key   TEXT NOT NULL PRIMARY KEY,
    value TEXT NOT NULL
);
"""

# Created after _merge_duplicate_cart_rows, which older databases may need.
CART_UNIQUE_INDEX = "CREATE UNIQUE INDEX IF NOT EXISTS cart_email_product ON cart (email, product_id)"


# (category, [(name, price, unit, shelf_life_days, stock), ...])
DEMO_CATALOG = [
    ("Fruits & Vegetables", [
        ("Apple", 180.0, "kg", 14, 60),
        ("Banana", 48.0, "kg", 5, 132),
        ("Carrot", 40.0, "kg", 10, 58),
        ("Pineapple", 70.0, "piece", 7, 19),
        ("Strawberry", 150.0, "pack", 4, 9),
    ]),
    ("Cold Drinks", [
        ("Pepsi", 40.0, "bottle", 180, 97),
        ("Sprite", 40.0, "bottle", 180, 8),
    ]),
    ("Dairy", [
        ("Milk", 54.0, "litre", 3, 120),
        ("Paneer", 90.0, "pack", 7, 50),
    ]),
    ("Poultry", [
        ("Chicken", 260.0, "kg", 3, 44),
        ("Egg", 7.0, "piece", 14, 1445),
    ]),
    ("Snacks", [
        ("Maggi", 14.0, "packet", 270, 50),
        ("Munch", 10.0, "packet", 120, 499),
        ("Top Ramen", 35.0, "packet", 270, 400),
    ]),
]

DEMO_COUPONS = [("FIRST50", 50.0), ("SAVE20", 20.0)]

# Demo accounts so visitors can try every role without signing up.
DEMO_USER = ("demo@grocery.app", "demo1234", "Demo Shopper", "1234567890", "221B Baker Street")
DEMO_MANAGER = ("manager@grocery.app", "manager1234", "Demo Manager", "9876543210", "742 Evergreen Terrace")


log = logging.getLogger(__name__)

# Foreign-key enforcement (PRAGMA foreign_keys) is deliberately left OFF:
# deleting a category removes its products while `inventory` and `cart` rows
# still reference them, and deleting a product leaves `cart` rows pointing at
# it. With enforcement on, those admin/manager delete flows would fail with
# "FOREIGN KEY constraint failed". The REFERENCES clauses document intent only.


def _database_path():
    return current_app.config["DATABASE_PATH"]


def _connect(path, config, **kwargs):
    # `timeout` sets SQLite's busy timeout: wait for locks instead of failing
    # immediately with "database is locked".
    return sqlite3.connect(path, timeout=config.get("SQLITE_BUSY_TIMEOUT", 15), **kwargs)


def get_db():
    """One connection per request/app context, closed by ``close_db``.

    Connections are never shared between threads: each gunicorn thread handles
    a request in its own app context, so sqlite3's ``check_same_thread`` default
    is kept on as a safety net.
    """
    if "db" not in g:
        g.db = _connect(_database_path(), current_app.config)
        # WAL is persisted in the file by init_db; NORMAL is safe with WAL
        # and avoids an fsync on every commit.
        g.db.execute("PRAGMA synchronous=NORMAL")
    return g.db


def close_db(exception=None):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def get_db_instance_id(db=None):
    """Random id of this database file, generated when it was created.

    Every auth token carries it, so tokens issued against a database that has
    since been wiped (redeploy, restart on an ephemeral disk) are rejected.
    """
    row = (db or get_db()).execute("SELECT value FROM meta WHERE key = 'db_instance_id'").fetchone()
    return row[0] if row else None


def _merge_duplicate_cart_rows(cur):
    """Collapse duplicate (email, product_id) cart rows into one, summing the
    quantities, so the unique index can be created on older databases."""
    if cur.execute("SELECT 1 FROM sqlite_master WHERE type = 'index' AND name = 'cart_email_product'").fetchone():
        return
    cur.execute(
        """UPDATE cart SET quantity = (SELECT SUM(c2.quantity) FROM cart c2
                                        WHERE c2.email = cart.email AND c2.product_id = cart.product_id)
           WHERE cartID IN (SELECT MIN(cartID) FROM cart GROUP BY email, product_id HAVING COUNT(*) > 1)"""
    )
    cur.execute("DELETE FROM cart WHERE cartID NOT IN (SELECT MIN(cartID) FROM cart GROUP BY email, product_id)")
    if cur.rowcount:
        log.info("Merged %d duplicate cart rows", cur.rowcount)


def _schema_statements():
    return [stmt.strip() for stmt in SCHEMA.split(";") if stmt.strip()]


def _enable_wal(conn, timeout):
    """Switch to WAL (persisted in the file). Changing the journal mode needs an
    exclusive lock and SQLite doesn't always apply the busy timeout to it, so
    retry while another process holds the database."""
    deadline = time.monotonic() + timeout
    while True:
        try:
            mode = conn.execute("PRAGMA journal_mode").fetchone()[0].lower()
            if mode == "wal":
                return mode
            return conn.execute("PRAGMA journal_mode=WAL").fetchone()[0].lower()
        except sqlite3.OperationalError as exc:
            if "locked" not in str(exc) or time.monotonic() > deadline:
                raise
            time.sleep(0.05)


def init_db(app):
    """Create the database (schema + demo data) if it doesn't exist yet.

    Safe to run from several processes at once (web server, Celery worker and
    beat all import the app): the whole check-create-seed sequence runs in one
    ``BEGIN IMMEDIATE`` transaction, so the second process waits for the
    first and then sees the tables already exist instead of seeding twice.
    """
    path = app.config["DATABASE_PATH"]
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)

    conn = _connect(path, app.config, isolation_level=None)  # manual transaction control
    try:
        # Readers don't block the writer (and vice versa) in WAL mode.
        mode = _enable_wal(conn, app.config.get("SQLITE_BUSY_TIMEOUT", 15))
        if mode != "wal":
            log.warning("SQLite journal_mode is %s (WAL not supported on this filesystem?)", mode)

        conn.execute("BEGIN IMMEDIATE")
        try:
            fresh = conn.execute(
                "SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = 'users'"
            ).fetchone() is None
            for statement in _schema_statements():
                conn.execute(statement)
            cur = conn.cursor()
            _merge_duplicate_cart_rows(cur)
            cur.execute(CART_UNIQUE_INDEX)
            # Inside the same IMMEDIATE transaction, so concurrent starters agree
            # on one id; also backfills databases created before the meta table.
            cur.execute("INSERT OR IGNORE INTO meta (key, value) VALUES ('db_instance_id', ?)",
                        (secrets.token_hex(16),))
            # The admin account is whatever ADMIN_USERNAME says now; drop any
            # account left over from an earlier ADMIN_USERNAME.
            admin = app.config["ADMIN_USERNAME"]
            cur.execute("DELETE FROM managers WHERE email <> ?", (admin,))
            cur.execute(
                "INSERT OR REPLACE INTO managers (email, password) VALUES (?, ?)",
                (admin, generate_password_hash(app.config["ADMIN_PASSWORD"])),
            )
            if fresh:
                _seed(cur)
            conn.execute("COMMIT")
        except BaseException:
            conn.execute("ROLLBACK")
            raise
    finally:
        conn.close()

    if fresh:
        log.info("Created new database with demo data at %s", path)
    else:
        log.info("Using existing database at %s", path)


def _seed(cur):
    today = date.today()
    for category, products in DEMO_CATALOG:
        cur.execute("INSERT INTO categories (category_name) VALUES (?)", (category,))
        category_id = cur.lastrowid
        for name, price, unit, shelf_life, stock in products:
            cur.execute(
                "INSERT INTO products (name, manufacture_date, expiry_date, price, categoryID, unit) "
                "VALUES (?, ?, ?, ?, ?, ?)",
                (name, (today - timedelta(days=1)).isoformat(),
                 (today + timedelta(days=shelf_life)).isoformat(), price, category_id, unit),
            )
            cur.execute("INSERT INTO inventory (productID, quantity) VALUES (?, ?)", (cur.lastrowid, stock))

    cur.executemany("INSERT INTO coupons (coupon_code, discount_percentage) VALUES (?, ?)", DEMO_COUPONS)

    for email, password, name, phone, address in (DEMO_USER, DEMO_MANAGER):
        cur.execute("INSERT INTO users (email, password) VALUES (?, ?)", (email, generate_password_hash(password)))
        cur.execute(
            "INSERT INTO user_profiles (email, name, address, phone) VALUES (?, ?, ?, ?)",
            (email, name, address, phone),
        )
    cur.execute("INSERT INTO store_manager (email, manager_status) VALUES (?, 'approved')", (DEMO_MANAGER[0],))
