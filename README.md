# 🍽️ 繁體中文智能線上點餐與出餐管理系統

一套專為現代茶飲與餐飲小館打造的完整、現代、高可用繁體中文 Web 點餐與門市管理系統。具備顧客線上點餐、即時購物車、現金/銀行轉帳對帳、廚房出餐工作站 (KDS)、訂單總表與付款核對、商品上下架管理及真實 SQLite 資料庫持久化儲存。

---

## 🌟 系統亮點與功能全覽

### 1. 🍜 顧客線上點餐 (Customer Ordering)
- **多分類選單**：支援「🍵 精選茶飲」、「🍚 經典飯食」、「🥟 主廚小點」等分類導覽與即時關鍵字搜尋。
- **餐點圖片與離線容錯**：每道餐點均具備高畫質美食攝影圖，若遇離線或網路不穩自動降級為手繪風格向量插圖，絕不破圖。
- **細緻客製化規格**：
  - 茶飲類：甜度 (正常糖/半糖/微糖/無糖)、冰塊 (正常冰/少冰/去冰/溫熱)、加料 (黑糖珍珠 +10元、手工仙草凍 +10元)。
  - 飯食類：飯量 (正常/半飯/加飯 +15元)、辣度 (不辣/微辣/小辣/大辣)、配菜微調 (不加蔥蒜/不要香菜)。
  - 點心類：調味醬料選擇 (蒜蓉醬/胡椒鹽/甜辣醬)。
- **購物車抽屜 (Shopping Cart)**：即時計算件數、單價、加料加價與總金額，支援數量即時增減與單項刪除。
- **多元結帳 (Checkout)**：
  - 用餐方式：**內用**（可選擇或輸入桌號）與**外帶**。
  - 付款方式：
    - **💵 現金結帳**：提醒顧客出示單號至櫃檯付款或送餐時交付。
    - **🏧 銀行轉帳**：自動展示門市匯款帳戶資訊（銀行代碼、帳號、戶名、一鍵複製帳號按鈕），並提供填寫「轉帳帳號後五碼」以利店家快速對帳。
- **下單即時追蹤 (Order Tracking)**：建立訂單後產生獨立編號（如 `#A001`），並具備四階段進度條（製作中 ➔ 完成待取 ➔ 已取餐）與付款核對狀態即時顯示。

### 2. 👨‍🍳 廚房出餐看板 (Kitchen Display System - KDS)
- **觸控平板/大螢幕最適化**：高對比度卡片排版、大字體餐點名稱與加料備註高亮，專為廚房料理台設計。
- **即時出餐流程推進**：
  - `製作中` ➔ 點擊「完成製作」一鍵推進為 `待取`（綠色高亮）。
  - `待取` ➔ 點擊「客人已取餐」一鍵完成出餐歸檔至 `已取`。
- **時間監控計時器**：每張票券即時計算經過時間（例如：`⏱️ 3 分鐘前`），逾時過久即時告警。
- **新單鈴聲提示**：內建 Web Audio API 雙音和弦清脆門市提單鈴聲，無需外部音檔即可發聲，並支援鈴聲試聽與開關。
- **自動同步**：每 5 秒背景輪詢，新訂單自動湧入。

### 3. 📋 訂單總表與付款核對 (Cashier POS & Payment Audit)
- **即時營運指標儀表板**：今日訂單總金額、實收金額、今日總單數、廚房待處理單數、待核對款項數。
- **付款核對專區**：
  - 明顯標示 `🔴 尚未確認` 與 `🟢 已付款`。
  - 轉帳訂單直接標明顧客回報之「轉帳末5碼」。
  - 店長可一鍵點擊「確認已收款」，狀態立刻寫入資料庫，避免漏單漏款。
- **靈活查詢與過濾**：支援搜尋訂單編號、顧客姓名、手機電話、桌號，並可按出餐狀態與付款方式分類篩選。
- **訂單管理**：支援出餐狀態下拉更新、查看完整餐點與備註明細、刪除/作廢訂單。

### 4. 🏷️ 商品菜單管理（店家自訂商品與上傳圖片）
- **店家自行上架新商品**：自訂商品名稱、所屬分類、販售單價、食材美味描述。
- **本地圖片檔案拖曳上傳**：
  - 支援從電腦或手機選擇圖片或直接拖曳檔案上傳（支援 JPG、PNG、WEBP、GIF）。
  - 自動存檔至伺服器靜態資源庫，並於前端即時預覽、更換或移除。
  - 亦可直接輸入網路圖片 URL。
- **自訂分類管理**：店家可自由建立專屬分類（如「手作甜點」、「特調氣泡飲」、「主廚便當」），隨時新增、修改與刪除。
- **彈性客製化規格編輯器**：
  - 店家可自由新增多組規格群組（如「甜度」、「冰塊」、「配料加價」、「份量加大」）。
  - 支援加價標註（如 `加珍珠 (+10元)`、`大碗 (+15元)`）。
  - 亦提供一鍵套用茶飲、飯食、點心標準規格範本。
- **一鍵清空範例商品**：讓店家一鍵清空所有預設範例，直接從 0 開始建立屬於自己的店鋪菜單；亦提供「恢復示範商品」功能隨時重新參考。
- **即時上下架切換 (Toggle Switch)**：一鍵切換「上架中」與「已下架 (暫停供應)」，無需重新整理，顧客端即時同步。

### 5. ⚙️ 門市設定 (Store Settings)
- 店名、宣傳標語、電話、地址設定。
- 銀行匯款資訊配置（銀行代碼、銀行帳號、帳戶戶名）。
- 內用桌號清單配置（以逗號分隔，隨時增減包廂或桌號）。
- 顧客點餐需知公告維護。

### 6. 🗄️ 真實資料庫與持久儲存 (Persistent Database)
- 採用 SQLite 本地資料庫檔案 (`restaurant.db`)，開啟 WAL (Write-Ahead Logging) 高併發讀寫模式。
- 完整的關聯式架構：`users`, `categories`, `products`, `orders`, `order_items`, `settings`。
- 重整網頁、重啟伺服器、電腦重開機，所有訂單、商品上下架狀態與款項紀錄 **100% 永久保留**。

### 7. 🔐 角色與權限隔離 (Authentication & RBAC)
- 採用標準 JWT Bearer 憑證與 PBKDF2 安全雜湊。
- 三級身分隔離：
  - **客人 (Guest)**：免登入即可點餐、查看購物車、查詢個人訂單；完全無法存取後台管理與廚房端 API (HTTP 401 攔截)。
  - **廚房人員 (Kitchen)**：僅可進入「廚房出餐看板 (KDS)」與查詢出餐明細；禁止修改商品菜單或門市設定 (HTTP 403 攔截)。
  - **店家店長 (Admin)**：全系統最高權限，可管理所有訂單、核對款項、新增/修改/下架商品、上傳圖片、修改門市營運設定。

---

## 🚀 快速啟動方式

本專案位於 `/Users/urista/restaurant-ordering-system`。

### 啟動伺服器
進入專案目錄執行啟動腳本：
```bash
cd /Users/urista/restaurant-ordering-system
./start.sh
```
或直接使用虛擬環境啟動：
```bash
cd /Users/urista/restaurant-ordering-system
.venv/bin/uvicorn server:app --host 0.0.0.0 --port 8000 --reload
```

啟動後即可在瀏覽器開啟：
👉 **http://127.0.0.1:8000** 或 **http://localhost:8000**

---

## 🔑 預設登入帳號密碼

登入視窗內已貼心設計「快速填入」按鈕，點擊即可一秒帶入：

| 角色 | 帳號 | 密碼 | 可存取頁面與權限 |
| :--- | :--- | :--- | :--- |
| **👑 店長（管理者）** | `admin` | `admin123` | **全部功能**：顧客點餐、廚房出餐、訂單總表、收款核對、商品管理（增修刪/上下架/傳圖）、門市設定、營業額統計 |
| **👨‍🍳 廚房出餐料理台** | `kitchen` | `kitchen123` | **出餐工作站**：出餐看板 (KDS)、訂單狀態推進 (製作中 ➔ 待取 ➔ 已取)、檢視餐點明細 |
| **🍜 一般顧客** | *(免登入)* | *(免登入)* | 瀏覽菜單、選配客製選項、購物車、送出訂單（現金/轉帳）、追蹤個人出餐進度 |

---

## 🧪 功能測試與驗證流程

系統內附完整端對端自動化測試程式，可在終端機執行：

```bash
cd /Users/urista/restaurant-ordering-system
python3 -c "
import urllib.request, json
BASE = 'http://127.0.0.1:8000'
def req(url, data=None, headers={}, method=None):
    if data:
        data = json.dumps(data).encode()
        headers['Content-Type'] = 'application/json'
    r = urllib.request.Request(url, data=data, headers=headers, method=method)
    with urllib.request.urlopen(r) as resp:
        return json.loads(resp.read().decode())

# 1. 廚房登入
k = req(f'{BASE}/api/auth/login', {'username': 'kitchen', 'password': 'kitchen123'})
print('✓ 廚房登入成功，角色:', k['user']['role'])

# 2. 客人線上點餐
order = req(f'{BASE}/api/orders', {
    'customer_name': '林小明',
    'customer_phone': '0912-345-678',
    'dining_type': '內用',
    'table_no': '3桌',
    'payment_method': '轉帳',
    'payment_note': '末五碼: 12345',
    'items': [{'product_id': 1, 'quantity': 1, 'selected_options': '甜度:微糖 / 冰塊:去冰'}]
})
print('✓ 客人成功下單：單號 #', order['order']['order_no'])

# 3. 廚房推進狀態
req(f'{BASE}/api/kitchen/orders/{order[\"order\"][\"id\"]}/step', headers={'Authorization': f'Bearer {k[\"token\"]}'}, method='POST')
print('✓ 廚房成功將訂單推進至待取狀態')

# 4. 店長登入核對付款
a = req(f'{BASE}/api/auth/login', {'username': 'admin', 'password': 'admin123'})
req(f'{BASE}/api/orders/{order[\"order\"][\"id\"]}/payment', {'payment_status': '已付款'}, headers={'Authorization': f'Bearer {a[\"token\"]}'}, method='PATCH')
print('✓ 店長成功核對款項並標記為已付款！')
"
```

---

## 📁 專案檔案結構

```
restaurant-ordering-system/
├── server.py              # FastAPI 主後端 API 與靜態路由
├── database.py            # SQLite 資料庫連線、Schema 與種子資料初始化
├── auth.py                # JWT Token 簽發驗證與 RBAC 權限裝飾器
├── restaurant.db          # 真正持久化的 SQLite 資料庫檔案
├── start.sh               # 單鍵啟動腳本
├── README.md              # 系統完整說明文件
└── static/
    ├── index.html         # Vue 3 + Tailwind CSS 單頁應用 (SPA) 前端
    ├── sound.js           # Web Audio API 廚房提單鈴聲模組
    ├── uploads/           # 店家自訂上傳商品圖庫目錄
    └── images/            # 本地預設向量美食插圖 (斷網備援)
        ├── tea_default.svg
        ├── rice_default.svg
        └── snack_default.svg
```
