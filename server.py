import os
import json
import uuid
import shutil
from datetime import datetime
from typing import List, Optional

from fastapi import FastAPI, HTTPException, Depends, UploadFile, File, Form, Query, status
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel, Field

from database import get_db, init_db, hash_password, verify_password
from auth import create_access_token, get_current_user, require_roles, get_current_user_optional

app = FastAPI(title="智能線上點餐與出餐管理系統", version="1.0.0")

# CORS 設定
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

BASE_DIR = os.path.dirname(__file__)
STATIC_DIR = os.path.join(BASE_DIR, "static")
UPLOAD_DIR = os.path.join(STATIC_DIR, "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)

# 初始化資料庫
@app.on_event("startup")
def on_startup():
    init_db()

# --- Pydantic 模型定義 ---

class LoginRequest(BaseModel):
    username: str
    password: str

class OrderItemRequest(BaseModel):
    product_id: int
    quantity: int = Field(gt=0)
    selected_options: Optional[str] = ""

class CreateOrderRequest(BaseModel):
    customer_name: str = Field(min_length=1)
    customer_phone: Optional[str] = ""
    dining_type: Optional[str] = ""
    table_no: Optional[str] = ""
    payment_method: str = Field(pattern="^(現金|轉帳)$")
    payment_note: Optional[str] = ""
    notes: Optional[str] = ""
    items: List[OrderItemRequest]

class UpdateOrderStatusRequest(BaseModel):
    order_status: str = Field(pattern="^(製作中|完成|待取|已取|已取消)$")

class UpdatePaymentRequest(BaseModel):
    payment_status: str = Field(pattern="^(尚未確認|已付款)$")
    payment_note: Optional[str] = None

class ProductCreateRequest(BaseModel):
    category_id: int
    name: str = Field(min_length=1)
    price: int = Field(gt=0)
    description: Optional[str] = ""
    image_url: Optional[str] = ""
    is_available: int = 1
    customization_options: Optional[str] = "[]"

class ProductUpdateRequest(BaseModel):
    category_id: Optional[int] = None
    name: Optional[str] = None
    price: Optional[int] = None
    description: Optional[str] = None
    image_url: Optional[str] = None
    is_available: Optional[int] = None
    customization_options: Optional[str] = None

class CategoryCreateRequest(BaseModel):
    name: str = Field(min_length=1)
    icon: Optional[str] = "utensils"
    sort_order: Optional[int] = 0

class CategoryUpdateRequest(BaseModel):
    name: Optional[str] = None
    icon: Optional[str] = None
    sort_order: Optional[int] = None
    is_active: Optional[int] = None

class SettingsUpdateRequest(BaseModel):
    settings: dict

class RecipeSaveRequest(BaseModel):
    product_id: int
    water_amount: Optional[str] = ""
    instructions: Optional[str] = ""
    tea_leaves_amount: Optional[str] = ""
    tea_leaves_ratio: Optional[str] = ""
    tea_leaves_note: Optional[str] = ""
    tea_leaves_image: Optional[str] = ""
    sugar_amount: Optional[str] = ""
    sugar_ratio: Optional[str] = ""
    sugar_note: Optional[str] = ""
    sugar_image: Optional[str] = ""
    milk_amount: Optional[str] = ""
    milk_ratio: Optional[str] = ""
    milk_note: Optional[str] = ""
    milk_image: Optional[str] = ""
    ice_amount: Optional[str] = ""
    ice_ratio: Optional[str] = ""
    ice_note: Optional[str] = ""
    ice_image: Optional[str] = ""
    fructose_amount: Optional[str] = ""
    fructose_ratio: Optional[str] = ""
    fructose_note: Optional[str] = ""
    fructose_image: Optional[str] = ""
    concentrate_amount: Optional[str] = ""
    concentrate_ratio: Optional[str] = ""
    concentrate_note: Optional[str] = ""
    concentrate_image: Optional[str] = ""

# --- 1. 認證相關 API ---

@app.post("/api/auth/login")
def login(req: LoginRequest):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE username = ?", (req.username.strip(),))
    user = cursor.fetchone()
    conn.close()

    if not user or not verify_password(req.password, user["password_hash"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="帳號或密碼錯誤，請重新確認"
        )

    token = create_access_token(
        user_id=user["id"],
        username=user["username"],
        role=user["role"],
        name=user["name"]
    )

    return {
        "success": True,
        "token": token,
        "user": {
            "id": user["id"],
            "username": user["username"],
            "name": user["name"],
            "role": user["role"]
        }
    }

@app.get("/api/auth/me")
def get_me(user: dict = Depends(get_current_user)):
    return {
        "success": True,
        "user": user
    }

# --- 2. 系統設定 API ---

@app.get("/api/settings")
def get_settings():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT key, value FROM settings")
    rows = cursor.fetchall()
    conn.close()
    return {row["key"]: row["value"] for row in rows}

@app.put("/api/settings")
def update_settings(req: SettingsUpdateRequest, user: dict = Depends(require_roles("admin"))):
    conn = get_db()
    cursor = conn.cursor()
    for k, v in req.settings.items():
        cursor.execute("INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)", (k, str(v)))
    conn.commit()
    conn.close()
    return {"success": True, "message": "店家設定已成功更新"}

# --- 3. 分類與菜單 (訪客 & 管理員) ---

@app.get("/api/categories")
def get_categories():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM categories WHERE is_active = 1 ORDER BY sort_order ASC, id ASC")
    rows = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return rows

@app.post("/api/admin/categories")
def create_category(req: CategoryCreateRequest, user: dict = Depends(require_roles("admin"))):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO categories (name, icon, sort_order) VALUES (?, ?, ?)",
                   (req.name.strip(), req.icon or "utensils", req.sort_order or 0))
    new_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return {"success": True, "id": new_id, "message": "分類新增成功"}

@app.put("/api/admin/categories/{cat_id}")
def update_category(cat_id: int, req: CategoryUpdateRequest, user: dict = Depends(require_roles("admin"))):
    conn = get_db()
    cursor = conn.cursor()
    fields = []
    values = []
    if req.name is not None:
        fields.append("name = ?")
        values.append(req.name.strip())
    if req.icon is not None:
        fields.append("icon = ?")
        values.append(req.icon)
    if req.sort_order is not None:
        fields.append("sort_order = ?")
        values.append(req.sort_order)
    if req.is_active is not None:
        fields.append("is_active = ?")
        values.append(req.is_active)
    if fields:
        values.append(cat_id)
        cursor.execute(f"UPDATE categories SET {', '.join(fields)} WHERE id = ?", values)
        conn.commit()
    conn.close()
    return {"success": True, "message": "分類已更新"}

@app.delete("/api/admin/categories/{cat_id}")
def delete_category(cat_id: int, user: dict = Depends(require_roles("admin"))):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) as cnt FROM products WHERE category_id = ?", (cat_id,))
    cnt = cursor.fetchone()["cnt"]
    if cnt > 0:
        conn.close()
        raise HTTPException(status_code=400, detail=f"此分類下尚有 {cnt} 個商品，請先將商品移動至其他分類或刪除商品後再刪除此分類")
    cursor.execute("DELETE FROM categories WHERE id = ?", (cat_id,))
    conn.commit()
    conn.close()
    return {"success": True, "message": "分類已成功刪除"}


@app.get("/api/products")
def get_products(category_id: Optional[int] = None):
    conn = get_db()
    cursor = conn.cursor()
    query = """
    SELECT p.*, c.name as category_name
    FROM products p
    JOIN categories c ON p.category_id = c.id
    WHERE p.is_available = 1
    """
    params = []
    if category_id:
        query += " AND p.category_id = ?"
        params.append(category_id)
    query += " ORDER BY p.category_id ASC, p.id ASC"

    cursor.execute(query, params)
    rows = []
    for r in cursor.fetchall():
        d = dict(r)
        try:
            d["customization_options"] = json.loads(d["customization_options"]) if d["customization_options"] else []
        except Exception:
            d["customization_options"] = []
        rows.append(d)
    conn.close()
    return rows

# 管理員商品列表（含已下架商品）
@app.get("/api/admin/products")
def get_admin_products(user: dict = Depends(require_roles("admin"))):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
    SELECT p.*, c.name as category_name
    FROM products p
    JOIN categories c ON p.category_id = c.id
    ORDER BY p.category_id ASC, p.id ASC
    """)
    rows = []
    for r in cursor.fetchall():
        d = dict(r)
        try:
            d["customization_options"] = json.loads(d["customization_options"]) if d["customization_options"] else []
        except Exception:
            d["customization_options"] = []
        rows.append(d)
    conn.close()
    return rows

@app.post("/api/admin/products")
def create_product(req: ProductCreateRequest, user: dict = Depends(require_roles("admin"))):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
    INSERT INTO products (category_id, name, price, description, image_url, is_available, customization_options)
    VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (req.category_id, req.name.strip(), req.price, req.description, req.image_url, req.is_available, req.customization_options))
    new_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return {"success": True, "id": new_id, "message": "商品新增成功"}

@app.put("/api/admin/products/{product_id}")
def update_product(product_id: int, req: ProductUpdateRequest, user: dict = Depends(require_roles("admin"))):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM products WHERE id = ?", (product_id,))
    prod = cursor.fetchone()
    if not prod:
        conn.close()
        raise HTTPException(status_code=404, detail="找不到指定商品")

    fields = []
    values = []
    if req.category_id is not None:
        fields.append("category_id = ?")
        values.append(req.category_id)
    if req.name is not None:
        fields.append("name = ?")
        values.append(req.name.strip())
    if req.price is not None:
        fields.append("price = ?")
        values.append(req.price)
    if req.description is not None:
        fields.append("description = ?")
        values.append(req.description)
    if req.image_url is not None:
        fields.append("image_url = ?")
        values.append(req.image_url)
    if req.is_available is not None:
        fields.append("is_available = ?")
        values.append(req.is_available)
    if req.customization_options is not None:
        fields.append("customization_options = ?")
        values.append(req.customization_options)

    if fields:
        fields.append("updated_at = CURRENT_TIMESTAMP")
        values.append(product_id)
        sql = f"UPDATE products SET {', '.join(fields)} WHERE id = ?"
        cursor.execute(sql, values)
        conn.commit()

    conn.close()
    return {"success": True, "message": "商品資訊已更新"}

@app.patch("/api/admin/products/{product_id}/toggle")
def toggle_product_availability(product_id: int, user: dict = Depends(require_roles("admin"))):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT is_available FROM products WHERE id = ?", (product_id,))
    prod = cursor.fetchone()
    if not prod:
        conn.close()
        raise HTTPException(status_code=404, detail="找不到指定商品")

    new_status = 0 if prod["is_available"] == 1 else 1
    cursor.execute("UPDATE products SET is_available = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?", (new_status, product_id))
    conn.commit()
    conn.close()
    return {"success": True, "is_available": new_status, "message": "已成功更新商品上下架狀態"}

@app.delete("/api/admin/products/{product_id}")
def delete_product(product_id: int, user: dict = Depends(require_roles("admin"))):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM products WHERE id = ?", (product_id,))
    if cursor.rowcount == 0:
        conn.close()
        raise HTTPException(status_code=404, detail="找不到指定商品")
    conn.commit()
    conn.close()
    return {"success": True, "message": "商品已刪除"}

@app.post("/api/admin/upload-image")
@app.post("/api/kitchen/upload-image")
async def upload_image(file: UploadFile = File(...), user: dict = Depends(require_roles("admin", "kitchen"))):
    allowed_exts = {".jpg", ".jpeg", ".png", ".webp", ".gif", ".svg"}
    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in allowed_exts:
        raise HTTPException(status_code=400, detail="只支援 JPG, PNG, WEBP, GIF, SVG 格式圖片")

    filename = f"{uuid.uuid4().hex[:12]}_{datetime.now().strftime('%Y%m%d%H%M%S')}{ext}"
    filepath = os.path.join(UPLOAD_DIR, filename)

    with open(filepath, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    return {
        "success": True,
        "url": f"/static/uploads/{filename}",
        "filename": filename
    }

# --- 4. 點餐與訂單 API ---

@app.post("/api/orders")
def create_order(req: CreateOrderRequest):
    if not req.items:
        raise HTTPException(status_code=400, detail="訂單不可為空，請至少選購一項商品")

    if req.dining_type and req.dining_type == "內用" and not req.table_no:
        raise HTTPException(status_code=400, detail="內用請務必選擇或填寫桌號")

    conn = get_db()
    cursor = conn.cursor()

    # 計算序號：產生今日唯一編號，如 A104
    cursor.execute("SELECT COUNT(*) as cnt FROM orders WHERE date(created_at, 'localtime') = date('now', 'localtime')")
    count_today = cursor.fetchone()["cnt"] + 1
    order_no = f"A{count_today:03d}"

    # 查核商品價格與計算總額
    total_amount = 0
    resolved_items = []
    for item_req in req.items:
        cursor.execute("SELECT id, name, price, is_available FROM products WHERE id = ?", (item_req.product_id,))
        prod = cursor.fetchone()
        if not prod:
            conn.close()
            raise HTTPException(status_code=400, detail=f"品項不存在 (ID: {item_req.product_id})")
        if prod["is_available"] == 0:
            conn.close()
            raise HTTPException(status_code=400, detail=f"商品「{prod['name']}」目前已下架，無法點購")

        # 計算額外加價（如有在 selected_options 標記加價）
        unit_price = prod["price"]
        extra = 0
        if item_req.selected_options and "+10元" in item_req.selected_options:
            extra += 10
        elif item_req.selected_options and "+15元" in item_req.selected_options:
            extra += 15

        item_price = unit_price + extra
        subtotal = item_price * item_req.quantity
        total_amount += subtotal

        resolved_items.append({
            "product_id": prod["id"],
            "product_name": prod["name"],
            "price": item_price,
            "quantity": item_req.quantity,
            "subtotal": subtotal,
            "selected_options": item_req.selected_options or ""
        })

    # 寫入訂單
    cursor.execute("""
    INSERT INTO orders (
        order_no, customer_name, customer_phone, dining_type, table_no,
        payment_method, payment_status, payment_note, order_status, total_amount, notes
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        order_no,
        req.customer_name.strip(),
        req.customer_phone.strip() if req.customer_phone else "",
        req.dining_type.strip() if req.dining_type else "",
        req.table_no.strip() if req.table_no else "",
        req.payment_method,
        "尚未確認",
        req.payment_note.strip() if req.payment_note else "",
        "製作中",
        total_amount,
        req.notes.strip() if req.notes else ""
    ))
    order_id = cursor.lastrowid

    # 寫入品項明細
    for it in resolved_items:
        cursor.execute("""
        INSERT INTO order_items (order_id, product_id, product_name, price, quantity, subtotal, selected_options)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (order_id, it["product_id"], it["product_name"], it["price"], it["quantity"], it["subtotal"], it["selected_options"]))

    conn.commit()

    # 回傳建立好的訂單
    cursor.execute("SELECT * FROM orders WHERE id = ?", (order_id,))
    new_order = dict(cursor.fetchone())
    new_order["items"] = resolved_items

    conn.close()
    return {
        "success": True,
        "message": "訂單建立成功！",
        "order": new_order
    }

@app.get("/api/orders/track/{order_no}")
def track_order(order_no: str):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM orders WHERE order_no = ?", (order_no.strip().upper(),))
    order = cursor.fetchone()
    if not order:
        conn.close()
        raise HTTPException(status_code=404, detail="查無此訂單編號")

    order_dict = dict(order)
    cursor.execute("SELECT * FROM order_items WHERE order_id = ?", (order_dict["id"],))
    order_dict["items"] = [dict(it) for it in cursor.fetchall()]
    conn.close()
    return order_dict

# --- 5. 廚房出餐專區 (KDS) ---

@app.get("/api/kitchen/orders")
def get_kitchen_orders(user: dict = Depends(require_roles("admin", "kitchen"))):
    conn = get_db()
    cursor = conn.cursor()
    # 廚房主要關注：製作中、完成、待取。並附上最近15分鐘內已取的訂單方便回溯。
    cursor.execute("""
    SELECT * FROM orders
    WHERE order_status IN ('製作中', '完成', '待取')
       OR (order_status = '已取' AND updated_at >= datetime('now', '-30 minutes'))
    ORDER BY
        CASE order_status
            WHEN '製作中' THEN 1
            WHEN '完成' THEN 2
            WHEN '待取' THEN 3
            WHEN '已取' THEN 4
            ELSE 5
        END,
        created_at ASC
    """)
    orders = [dict(row) for row in cursor.fetchall()]

    for o in orders:
        cursor.execute("SELECT * FROM order_items WHERE order_id = ?", (o["id"],))
        o["items"] = [dict(it) for it in cursor.fetchall()]

    conn.close()
    return orders

@app.post("/api/kitchen/orders/{order_id}/step")
def step_kitchen_order_status(order_id: int, user: dict = Depends(require_roles("admin", "kitchen"))):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM orders WHERE id = ?", (order_id,))
    order = cursor.fetchone()
    if not order:
        conn.close()
        raise HTTPException(status_code=404, detail="找不到指定訂單")

    current = order["order_status"]
    # 狀態流程：製作中 -> 完成待取 -> 已取
    next_status = current
    if current == "製作中":
        next_status = "待取"
    elif current in ("完成", "待取"):
        next_status = "已取"

    cursor.execute("UPDATE orders SET order_status = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?", (next_status, order_id))
    conn.commit()
    conn.close()
    return {"success": True, "previous_status": current, "order_status": next_status}

# --- 5.1 廚房茶葉製作配方管理 ---

def format_recipe(row, product_name="", product_image=""):
    keys = row.keys() if hasattr(row, "keys") else []
    p_name = product_name or (row["product_name"] if "product_name" in keys else "")
    p_img = product_image or (row["product_image"] if "product_image" in keys else "")
    return {
        "id": row["id"] if ("id" in keys) else (row["recipe_id"] if ("recipe_id" in keys) else None),
        "product_id": row["product_id"],
        "product_name": p_name,
        "product_image": p_img,
        "water_amount": row["water_amount"] or "",
        "instructions": row["instructions"] or "",
        "items": [
            {
                "key": "tea_leaves",
                "name": "茶葉量",
                "amount": row["tea_leaves_amount"] or "",
                "ratio": row["tea_leaves_ratio"] or "",
                "note": row["tea_leaves_note"] or "",
                "image": row["tea_leaves_image"] or "",
                "default_icon": "🍃",
                "color": "emerald"
            }
        ],
        "tea_leaves_amount": row["tea_leaves_amount"] or "",
        "tea_leaves_ratio": row["tea_leaves_ratio"] or "",
        "tea_leaves_note": row["tea_leaves_note"] or "",
        "tea_leaves_image": row["tea_leaves_image"] or "",
        "sugar_amount": "",
        "sugar_ratio": "",
        "sugar_note": "",
        "sugar_image": "",
        "milk_amount": "",
        "milk_ratio": "",
        "milk_note": "",
        "milk_image": "",
        "ice_amount": "",
        "ice_ratio": "",
        "ice_note": "",
        "ice_image": "",
        "fructose_amount": "",
        "fructose_ratio": "",
        "fructose_note": "",
        "fructose_image": "",
        "concentrate_amount": "",
        "concentrate_ratio": "",
        "concentrate_note": "",
        "concentrate_image": "",
        "updated_at": (row["updated_at"] or "") if "updated_at" in keys else ""
    }

@app.get("/api/recipes")
def get_all_recipes():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
    SELECT p.id as product_id, p.name as product_name, p.image_url as product_image,
           p.price, c.name as category_name,
           r.id as recipe_id,
           r.water_amount, r.instructions,
           r.tea_leaves_amount, r.tea_leaves_ratio, r.tea_leaves_note, r.tea_leaves_image,
           r.sugar_amount, r.sugar_ratio, r.sugar_note, r.sugar_image,
           r.milk_amount, r.milk_ratio, r.milk_note, r.milk_image,
           r.ice_amount, r.ice_ratio, r.ice_note, r.ice_image,
           r.fructose_amount, r.fructose_ratio, r.fructose_note, r.fructose_image,
           r.concentrate_amount, r.concentrate_ratio, r.concentrate_note, r.concentrate_image,
           r.updated_at
    FROM products p
    LEFT JOIN categories c ON p.category_id = c.id
    LEFT JOIN recipes r ON p.id = r.product_id
    ORDER BY p.category_id ASC, p.id ASC
    """)
    rows = cursor.fetchall()
    conn.close()
    result = []
    for row in rows:
        has_recipe = row["recipe_id"] is not None
        rec = format_recipe(row, row["product_name"], row["product_image"]) if has_recipe else None
        result.append({
            "product_id": row["product_id"],
            "product_name": row["product_name"],
            "product_image": row["product_image"] or "",
            "price": row["price"],
            "category_name": row["category_name"] or "",
            "has_recipe": has_recipe,
            "recipe_id": row["recipe_id"],
            "recipe": rec
        })
    return result

@app.get("/api/recipes/{product_id}")
def get_recipe_by_product(product_id: int):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT id, name, image_url FROM products WHERE id = ?", (product_id,))
    prod = cursor.fetchone()
    if not prod:
        conn.close()
        raise HTTPException(status_code=404, detail="找不到指定商品")

    cursor.execute("SELECT * FROM recipes WHERE product_id = ?", (product_id,))
    row = cursor.fetchone()
    conn.close()
    if not row:
        return {
            "has_recipe": False,
            "product_id": product_id,
            "product_name": prod["name"],
            "product_image": prod["image_url"] or "",
            "recipe": None
        }

    return {
        "has_recipe": True,
        "product_id": product_id,
        "product_name": prod["name"],
        "product_image": prod["image_url"] or "",
        "recipe": format_recipe(row, prod["name"], prod["image_url"])
    }

@app.post("/api/recipes")
@app.put("/api/recipes/{product_id}")
def save_or_update_recipe(req: RecipeSaveRequest, product_id: Optional[int] = None, user: dict = Depends(require_roles("admin", "kitchen"))):
    pid = product_id if product_id is not None else req.product_id
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT id, name, image_url FROM products WHERE id = ?", (pid,))
    prod = cursor.fetchone()
    if not prod:
        conn.close()
        raise HTTPException(status_code=404, detail="找不到指定商品")

    cursor.execute("""
    INSERT INTO recipes (
        product_id,
        tea_leaves_amount, tea_leaves_ratio, tea_leaves_note, tea_leaves_image,
        sugar_amount, sugar_ratio, sugar_note, sugar_image,
        milk_amount, milk_ratio, milk_note, milk_image,
        ice_amount, ice_ratio, ice_note, ice_image,
        fructose_amount, fructose_ratio, fructose_note, fructose_image,
        concentrate_amount, concentrate_ratio, concentrate_note, concentrate_image,
        water_amount, instructions, updated_at
    ) VALUES (
        ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP
    )
    ON CONFLICT(product_id) DO UPDATE SET
        tea_leaves_amount = excluded.tea_leaves_amount,
        tea_leaves_ratio = excluded.tea_leaves_ratio,
        tea_leaves_note = excluded.tea_leaves_note,
        tea_leaves_image = excluded.tea_leaves_image,
        sugar_amount = excluded.sugar_amount,
        sugar_ratio = excluded.sugar_ratio,
        sugar_note = excluded.sugar_note,
        sugar_image = excluded.sugar_image,
        milk_amount = excluded.milk_amount,
        milk_ratio = excluded.milk_ratio,
        milk_note = excluded.milk_note,
        milk_image = excluded.milk_image,
        ice_amount = excluded.ice_amount,
        ice_ratio = excluded.ice_ratio,
        ice_note = excluded.ice_note,
        ice_image = excluded.ice_image,
        fructose_amount = excluded.fructose_amount,
        fructose_ratio = excluded.fructose_ratio,
        fructose_note = excluded.fructose_note,
        fructose_image = excluded.fructose_image,
        concentrate_amount = excluded.concentrate_amount,
        concentrate_ratio = excluded.concentrate_ratio,
        concentrate_note = excluded.concentrate_note,
        concentrate_image = excluded.concentrate_image,
        water_amount = excluded.water_amount,
        instructions = excluded.instructions,
        updated_at = CURRENT_TIMESTAMP
    """, (
        pid,
        req.tea_leaves_amount or "", req.tea_leaves_ratio or "", req.tea_leaves_note or "", req.tea_leaves_image or "",
        req.sugar_amount or "", req.sugar_ratio or "", req.sugar_note or "", req.sugar_image or "",
        req.milk_amount or "", req.milk_ratio or "", req.milk_note or "", req.milk_image or "",
        req.ice_amount or "", req.ice_ratio or "", req.ice_note or "", req.ice_image or "",
        req.fructose_amount or "", req.fructose_ratio or "", req.fructose_note or "", req.fructose_image or "",
        req.concentrate_amount or "", req.concentrate_ratio or "", req.concentrate_note or "", req.concentrate_image or "",
        req.water_amount or "", req.instructions or ""
    ))
    conn.commit()

    cursor.execute("SELECT * FROM recipes WHERE product_id = ?", (pid,))
    updated_row = cursor.fetchone()
    conn.close()
    return {
        "success": True,
        "message": "配方儲存成功",
        "recipe": format_recipe(updated_row, prod["name"], prod["image_url"])
    }

@app.delete("/api/recipes/{product_id}")
def delete_recipe(product_id: int, user: dict = Depends(require_roles("admin", "kitchen"))):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM recipes WHERE product_id = ?", (product_id,))
    if cursor.rowcount == 0:
        conn.close()
        raise HTTPException(status_code=404, detail="找不到指定配方")
    conn.commit()
    conn.close()
    return {"success": True, "message": "商品配方已成功刪除"}

# --- 6. 訂單總表與付款核對 (店長與財務) ---

@app.get("/api/orders")
def get_all_orders(
    status: Optional[str] = None,
    payment_status: Optional[str] = None,
    payment_method: Optional[str] = None,
    search: Optional[str] = None,
    user: dict = Depends(require_roles("admin", "kitchen"))
):
    conn = get_db()
    cursor = conn.cursor()

    query = "SELECT * FROM orders WHERE 1=1"
    params = []

    if status and status != "全部":
        query += " AND order_status = ?"
        params.append(status)

    if payment_status and payment_status != "全部":
        query += " AND payment_status = ?"
        params.append(payment_status)

    if payment_method and payment_method != "全部":
        query += " AND payment_method = ?"
        params.append(payment_method)

    if search:
        search_like = f"%{search.strip()}%"
        query += " AND (order_no LIKE ? OR customer_name LIKE ? OR customer_phone LIKE ? OR table_no LIKE ?)"
        params.extend([search_like, search_like, search_like, search_like])

    query += " ORDER BY id DESC LIMIT 200"

    cursor.execute(query, params)
    orders = [dict(row) for row in cursor.fetchall()]

    for o in orders:
        cursor.execute("SELECT * FROM order_items WHERE order_id = ?", (o["id"],))
        o["items"] = [dict(it) for it in cursor.fetchall()]

    conn.close()
    return orders

@app.patch("/api/orders/{order_id}/status")
def update_order_status(order_id: int, req: UpdateOrderStatusRequest, user: dict = Depends(require_roles("admin", "kitchen"))):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("UPDATE orders SET order_status = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?", (req.order_status, order_id))
    if cursor.rowcount == 0:
        conn.close()
        raise HTTPException(status_code=404, detail="找不到指定訂單")
    conn.commit()
    conn.close()
    return {"success": True, "order_status": req.order_status, "message": "訂單出餐狀態已更新"}

@app.patch("/api/orders/{order_id}/payment")
def update_order_payment(order_id: int, req: UpdatePaymentRequest, user: dict = Depends(require_roles("admin"))):
    conn = get_db()
    cursor = conn.cursor()

    sql = "UPDATE orders SET payment_status = ?, updated_at = CURRENT_TIMESTAMP"
    params = [req.payment_status]

    if req.payment_note is not None:
        sql += ", payment_note = ?"
        params.append(req.payment_note)

    sql += " WHERE id = ?"
    params.append(order_id)

    cursor.execute(sql, params)
    if cursor.rowcount == 0:
        conn.close()
        raise HTTPException(status_code=404, detail="找不到指定訂單")

    conn.commit()
    conn.close()
    return {"success": True, "payment_status": req.payment_status, "message": "付款核對狀態已更新"}

@app.delete("/api/orders/{order_id}")
def delete_order(order_id: int, user: dict = Depends(require_roles("admin"))):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM orders WHERE id = ?", (order_id,))
    if cursor.rowcount == 0:
        conn.close()
        raise HTTPException(status_code=404, detail="找不到指定訂單")
    conn.commit()
    conn.close()
    return {"success": True, "message": "訂單已刪除"}

# --- 7. 營運統計數據 (店長專屬) ---

@app.get("/api/stats")
def get_stats(user: dict = Depends(require_roles("admin"))):
    conn = get_db()
    cursor = conn.cursor()

    # 今日總營收
    cursor.execute("SELECT COALESCE(SUM(total_amount), 0) as rev FROM orders WHERE date(created_at, 'localtime') = date('now', 'localtime')")
    today_revenue = cursor.fetchone()["rev"]

    # 今日已實收金額
    cursor.execute("SELECT COALESCE(SUM(total_amount), 0) as paid_rev FROM orders WHERE payment_status = '已付款' AND date(created_at, 'localtime') = date('now', 'localtime')")
    today_paid = cursor.fetchone()["paid_rev"]

    # 今日訂單總數
    cursor.execute("SELECT COUNT(*) as cnt FROM orders WHERE date(created_at, 'localtime') = date('now', 'localtime')")
    today_orders = cursor.fetchone()["cnt"]

    # 待出餐（製作中 + 完成待取）
    cursor.execute("SELECT COUNT(*) as cnt FROM orders WHERE order_status IN ('製作中', '完成', '待取')")
    pending_kitchen = cursor.fetchone()["cnt"]

    # 待核對款項（尚未確認付款）
    cursor.execute("SELECT COUNT(*) as cnt FROM orders WHERE payment_status = '尚未確認'")
    pending_payment = cursor.fetchone()["cnt"]

    conn.close()
    return {
        "today_revenue": today_revenue,
        "today_paid": today_paid,
        "today_orders": today_orders,
        "pending_kitchen": pending_kitchen,
        "pending_payment": pending_payment
    }

# --- 8. 靜態檔案掛載與入口頁面 ---

app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

@app.get("/")
def serve_index():
    return FileResponse(os.path.join(STATIC_DIR, "index.html"))

@app.get("/{full_path:path}")
def catch_all(full_path: str):
    # 若請求不存在的靜態資源，返回 index.html SPA
    file_path = os.path.join(STATIC_DIR, full_path)
    if os.path.exists(file_path) and os.path.isfile(file_path):
        return FileResponse(file_path)
    return FileResponse(os.path.join(STATIC_DIR, "index.html"))

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("server:app", host="0.0.0.0", port=port, reload=False)

