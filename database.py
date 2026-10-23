import sqlite3
import os
import json
import hashlib
import secrets
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(__file__), "restaurant.db")

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("PRAGMA journal_mode = WAL")
    return conn

def hash_password(password: str) -> str:
    salt = secrets.token_hex(16)
    h = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), 100000).hex()
    return f"{salt}:{h}"

def verify_password(password: str, stored_hash: str) -> bool:
    try:
        salt, h = stored_hash.split(":")
        calc = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), 100000).hex()
        return secrets.compare_digest(calc, h)
    except Exception:
        return False

def init_db():
    conn = get_db()
    cursor = conn.cursor()

    # 1. 建立使用者資料表
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        name TEXT NOT NULL,
        role TEXT NOT NULL, -- 'admin', 'kitchen'
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    # 2. 建立商品分類資料表
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS categories (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        icon TEXT DEFAULT 'utensils',
        sort_order INTEGER DEFAULT 0,
        is_active INTEGER DEFAULT 1
    )
    """)

    # 3. 建立商品菜單資料表
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS products (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        category_id INTEGER NOT NULL REFERENCES categories(id) ON DELETE CASCADE,
        name TEXT NOT NULL,
        price INTEGER NOT NULL,
        description TEXT DEFAULT '',
        image_url TEXT DEFAULT '',
        is_available INTEGER DEFAULT 1,
        customization_options TEXT DEFAULT '[]', -- JSON string
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    # 4. 建立訂單資料表
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS orders (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        order_no TEXT UNIQUE NOT NULL,
        customer_name TEXT NOT NULL,
        customer_phone TEXT DEFAULT '',
        dining_type TEXT NOT NULL, -- '內用', '外帶'
        table_no TEXT DEFAULT '',
        payment_method TEXT NOT NULL, -- '現金', '轉帳'
        payment_status TEXT NOT NULL DEFAULT '尚未確認', -- '尚未確認', '已付款'
        payment_note TEXT DEFAULT '', -- e.g. 轉帳末5碼
        order_status TEXT NOT NULL DEFAULT '製作中', -- '製作中', '完成', '待取', '已取', '已取消'
        total_amount INTEGER NOT NULL,
        notes TEXT DEFAULT '',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    # 5. 建立訂單明細資料表
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS order_items (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        order_id INTEGER NOT NULL REFERENCES orders(id) ON DELETE CASCADE,
        product_id INTEGER,
        product_name TEXT NOT NULL,
        price INTEGER NOT NULL,
        quantity INTEGER NOT NULL,
        subtotal INTEGER NOT NULL,
        selected_options TEXT DEFAULT ''
    )
    """)

    # 6. 建立系統設定資料表
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS settings (
        key TEXT PRIMARY KEY,
        value TEXT NOT NULL
    )
    """)

    # 7. 建立商品製作配方資料表 (六項比例製作圖)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS recipes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        product_id INTEGER UNIQUE NOT NULL REFERENCES products(id) ON DELETE CASCADE,
        tea_leaves_amount TEXT DEFAULT '',
        tea_leaves_ratio TEXT DEFAULT '',
        tea_leaves_note TEXT DEFAULT '',
        tea_leaves_image TEXT DEFAULT '',
        sugar_amount TEXT DEFAULT '',
        sugar_ratio TEXT DEFAULT '',
        sugar_note TEXT DEFAULT '',
        sugar_image TEXT DEFAULT '',
        milk_amount TEXT DEFAULT '',
        milk_ratio TEXT DEFAULT '',
        milk_note TEXT DEFAULT '',
        milk_image TEXT DEFAULT '',
        ice_amount TEXT DEFAULT '',
        ice_ratio TEXT DEFAULT '',
        ice_note TEXT DEFAULT '',
        ice_image TEXT DEFAULT '',
        fructose_amount TEXT DEFAULT '',
        fructose_ratio TEXT DEFAULT '',
        fructose_note TEXT DEFAULT '',
        fructose_image TEXT DEFAULT '',
        concentrate_amount TEXT DEFAULT '',
        concentrate_ratio TEXT DEFAULT '',
        concentrate_note TEXT DEFAULT '',
        concentrate_image TEXT DEFAULT '',
        water_amount TEXT DEFAULT '',
        instructions TEXT DEFAULT '',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    # 預設管理員與廚房帳號
    cursor.execute("SELECT COUNT(*) as cnt FROM users")
    if cursor.fetchone()["cnt"] == 0:
        cursor.execute("""
        INSERT INTO users (username, password_hash, name, role)
        VALUES (?, ?, ?, ?)
        """, ("admin", hash_password("admin123"), "店家管理者（店長）", "admin"))

        cursor.execute("""
        INSERT INTO users (username, password_hash, name, role)
        VALUES (?, ?, ?, ?)
        """, ("kitchen", hash_password("kitchen123"), "廚房出餐料理台", "kitchen"))

    # 預設設定
    default_settings = {
        "store_name": "線上點餐系統",
        "store_slogan": "現點現做 ‧ 精緻餐點茶飲",
        "store_phone": "",
        "store_address": "",
        "bank_name": "中國信託商業銀行 (822)",
        "bank_account": "",
        "bank_holder": "",
        "tables": "1桌,2桌,3桌,5桌,6桌,7桌,8桌,吧檯A,吧檯B",
        "order_notice": "歡迎光臨！餐點現點現做，約需 10-15 分鐘。若選擇轉帳，請於結帳時填寫帳號末五碼方便對帳。"
    }

    for k, v in default_settings.items():
        cursor.execute("INSERT OR IGNORE INTO settings (key, value) VALUES (?, ?)", (k, v))

    # 預設商品分類（提供基礎分類供店家選用，店家亦可自由增刪修改）
    cursor.execute("SELECT COUNT(*) as cnt FROM categories")
    if cursor.fetchone()["cnt"] == 0:
        default_categories = [
            ("紅茶", "coffee", 1),
            ("綠茶", "leaf", 2),
            ("白茶", "wind", 3),
            ("烏龍茶", "coffee", 4),
            ("草本茶", "flower", 5),
            ("點心", "cookie", 6)
        ]
        for name, icon, sort_order in default_categories:
            cursor.execute("INSERT INTO categories (name, icon, sort_order) VALUES (?, ?, ?)", (name, icon, sort_order))

    # 嚴格遵照需求：不自動產生任何預設商品、示範商品或假資料！
    # 網站初始時商品列表為空，全由店家管理者於商品管理後台自行新增。

    conn.commit()
    conn.close()

if __name__ == "__main__":
    init_db()
    print("Database schema initialized successfully (no demo products seeded).")
