# sl_hrm_line - LINE 打卡系統

## 模組概述

| 項目 | 值 |
|------|-----|
| 模組名稱 | LINE 打卡系統 |
| 技術名稱 | sl_hrm_line |
| 版本 | 19.0.1.0.0 |
| 類別 | Human Resources/Attendance |
| 路徑 | addons_store/sl_hrm_line |

LINE LIFF 員工綁定與 GPS 打卡系統，基於 Odoo 19 標準 HR 模組擴展。

## 功能

- **LINE 員工綁定** - 透過員工姓名綁定 LINE 帳號
- **GPS 打卡** - 上下班打卡記錄 GPS 座標
- **出勤歷史查詢** - 查詢員工出勤記錄

## 目錄結構

```
sl_hrm_line/
├── __init__.py
├── __manifest__.py
├── CLAUDE.md
├── models/
│   ├── __init__.py
│   ├── hr_employee.py      # 員工 LINE 綁定欄位
│   └── hr_attendance.py    # GPS 打卡方法
├── controllers/
│   ├── __init__.py
│   └── line_api.py         # REST API
├── views/
│   ├── hr_employee_views.xml
│   └── hr_attendance_views.xml
└── security/
    └── ir.model.access.csv
```

## 依賴模組

| 模組 | 說明 |
|------|------|
| base | 基礎模組 |
| hr | 人力資源模組 |
| hr_attendance | 出勤模組 |
| sl_hrm | Starry Lord HRM 整合模組 |

## API 端點

| 端點 | 方法 | 說明 |
|------|------|------|
| `/api/line/check-binding` | POST | 檢查 LINE 帳號是否已綁定 |
| `/api/line/bind` | POST | 員工綁定（用姓名） |
| `/api/line/user` | GET | 取得已綁定用戶資料 |
| `/api/line/attendance/today` | GET | 取得今日打卡狀態 |
| `/api/line/attendance/clock` | POST | 打卡（上班/下班） |
| `/api/line/attendance/history` | GET | 取得出勤歷史 |

**認證方式**: Header `X-Line-User-Id`

**支援 CORS**: 是

## hr.employee 擴展欄位

| 欄位 | 類型 | 說明 |
|------|------|------|
| line_user_id | Char | LINE User ID (indexed, unique) |
| line_display_name | Char | LINE 顯示名稱 |
| line_picture_url | Char | LINE 頭像 URL |
| line_binding_date | Datetime | LINE 綁定時間 (readonly) |
| is_line_bound | Boolean | 已綁定 LINE (computed, stored) |

## hr.employee 方法

| 方法 | 說明 |
|------|------|
| `_compute_is_line_bound()` | 計算是否已綁定 LINE |
| `action_unbind_line()` | 解除 LINE 綁定 |
| `get_employee_by_line_user_id(line_user_id)` | 透過 LINE User ID 取得員工 |
| `_get_employee_data()` | 取得員工資料（供 API 回傳） |

## hr.attendance 方法

| 方法 | 說明 |
|------|------|
| `get_today_status(employee_id)` | 取得員工今日打卡狀態 |
| `clock_action(employee_id, clock_type, latitude, longitude, accuracy)` | 執行打卡動作 |
| `get_attendance_history(employee_id, limit, offset)` | 取得出勤歷史記錄 |

## API 詳細說明

### POST /api/line/check-binding

檢查用戶是否已綁定

**Request Body:**
```json
{
    "userId": "LINE_USER_ID",
    "displayName": "用戶名稱",
    "pictureUrl": "頭像網址"
}
```

**Response (已綁定):**
```json
{
    "success": true,
    "isBound": true,
    "data": {
        "id": 1,
        "employee_id": 1,
        "name": "員工姓名",
        "department": "部門名稱",
        "department_id": 1,
        "job_title": "職稱",
        "work_email": "email@example.com",
        "work_phone": "123456789",
        "line_user_id": "LINE_USER_ID",
        "line_display_name": "LINE 名稱",
        "picture_url": "頭像網址"
    }
}
```

**Response (未綁定):**
```json
{
    "success": true,
    "isBound": false,
    "data": null
}
```

### POST /api/line/bind

員工綁定（用姓名）

**Request Body:**
```json
{
    "line_user_id": "LINE_USER_ID",
    "line_display_name": "LINE 名稱",
    "line_picture_url": "頭像網址",
    "employee_name": "員工姓名"
}
```

**Response (綁定成功):**
```json
{
    "success": true,
    "data": {
        "matched": true,
        "id": 1,
        "name": "員工姓名",
        ...
    }
}
```

**Response (找不到員工):**
```json
{
    "success": true,
    "data": {
        "matched": false
    }
}
```

### GET /api/line/user

取得用戶資料

**Header:** `X-Line-User-Id: LINE_USER_ID`

**Response:**
```json
{
    "success": true,
    "data": {
        "id": 1,
        "name": "員工姓名",
        ...
    }
}
```

### GET /api/line/attendance/today

取得今日打卡狀態

**Header:** `X-Line-User-Id: LINE_USER_ID`

**Response (已打卡):**
```json
{
    "success": true,
    "data": {
        "id": 1,
        "status": "clocked_in",
        "check_in": "2026-01-23 09:00:00",
        "check_in_time": "09:00",
        "check_out": null,
        "check_out_time": null,
        "check_in_latitude": 25.0330,
        "check_in_longitude": 121.5654,
        "check_out_latitude": null,
        "check_out_longitude": null
    }
}
```

**Response (未打卡):**
```json
{
    "success": true,
    "data": {
        "status": "not_clocked_in",
        "check_in": null,
        "check_out": null
    }
}
```

### POST /api/line/attendance/clock

打卡（上班/下班）

**Header:** `X-Line-User-Id: LINE_USER_ID`

**Request Body:**
```json
{
    "type": "in",
    "latitude": 25.0330,
    "longitude": 121.5654,
    "accuracy": 10
}
```

**Response:**
```json
{
    "success": true,
    "data": {
        "id": 1,
        "type": "in",
        "status": "clocked_in",
        "time": "09:00",
        "datetime": "2026-01-23 09:00:00",
        "latitude": 25.0330,
        "longitude": 121.5654
    }
}
```

### GET /api/line/attendance/history

取得出勤歷史

**Header:** `X-Line-User-Id: LINE_USER_ID`

**Query Parameters:**
- `limit`: 筆數限制 (default: 30)
- `offset`: 偏移量 (default: 0)

**Response:**
```json
{
    "success": true,
    "data": {
        "records": [
            {
                "id": 1,
                "date": "2026-01-23",
                "weekday": "四",
                "check_in": "09:00",
                "check_out": "18:00",
                "worked_hours": 9.0,
                "check_in_latitude": 25.0330,
                "check_in_longitude": 121.5654,
                "check_out_latitude": 25.0330,
                "check_out_longitude": 121.5654
            }
        ],
        "total": 100
    }
}
```

## 錯誤代碼

| 代碼 | 說明 |
|------|------|
| INVALID_JSON | 無效的 JSON 格式 |
| MISSING_USER_ID | 缺少 LINE User ID |
| MISSING_NAME | 缺少員工姓名 |
| ALREADY_BOUND | 此 LINE 帳號已綁定其他員工 |
| EMPLOYEE_BOUND | 此員工已綁定其他 LINE 帳號 |
| USER_NOT_FOUND | 用戶尚未綁定 |
| MODULE_NOT_INSTALLED | hr_attendance 模組尚未安裝 |
| ALREADY_CLOCKED_IN | 今日已打過上班卡 |
| NOT_CLOCKED_IN | 今日尚未打上班卡 |
| INVALID_TYPE | 無效的打卡類型 |
| SERVER_ERROR | 伺服器錯誤 |

## Odoo 19 升級說明

從 Odoo 17 升級注意事項：

1. **模型必須有 _description** - 所有 _inherit 的模型都加上 _description
2. **tree 改為 list** - 視圖 ID 命名使用 list 而非 tree
3. **attrs 改為直接屬性** - `invisible="not is_line_bound"` 直接寫在元素上
4. **GPS 欄位** - Odoo 19 內建 in_latitude, in_longitude, out_latitude, out_longitude

## 前端專案

對應前端：`line/line_hrm/` (Svelte 5 + Vite + Tailwind CSS + DaisyUI)

**路徑**: `D:\odoo\odoo19_euptop\line\line_hrm`

**啟動方式**:
```bash
cd D:\odoo\odoo19_euptop\line\line_hrm
npm install
cp .env.example .env
# 編輯 .env 設定 LIFF ID 和 API URL
npm run dev
```

## 測試案例

### 測試檔案位置

```
sl_hrm_line/tests/
├── __init__.py
├── test_hr_employee_line.py    # 員工 LINE 綁定測試
├── test_hr_attendance_line.py  # GPS 打卡測試
└── test_line_api.py            # REST API 測試
```

### 執行測試

```bash
# 執行所有測試
.venv\Scripts\python.exe D:\odoo\odoo_19\odoo-bin --config=D:\odoo\odoo_conf\odoo19-euptop.conf --database=odoo19_test --test-enable --stop-after-init -i sl_hrm_line

# 執行特定測試檔案
.venv\Scripts\python.exe D:\odoo\odoo_19\odoo-bin --config=D:\odoo\odoo_conf\odoo19-euptop.conf --database=odoo19_test --test-enable --stop-after-init -i sl_hrm_line --test-tags=/sl_hrm_line
```

### VS Code 偵錯設定

```json
{
    "name": "Test sl_hrm_line",
    "type": "debugpy",
    "request": "launch",
    "stopOnEntry": false,
    "python": ".venv\\Scripts\\python.exe",
    "console": "integratedTerminal",
    "program": "D:\\odoo\\odoo_19\\odoo-bin",
    "args": [
        "--config=D:\\odoo\\odoo_conf\\odoo19-euptop.conf",
        "--database=odoo19_test",
        "--http-port=8019",
        "--test-enable",
        "--stop-after-init",
        "-i", "sl_hrm_line"
    ],
    "cwd": "${workspaceRoot}"
}
```

### 測試案例說明

#### test_hr_employee_line.py

| 測試方法 | 說明 |
|----------|------|
| `test_line_binding` | 測試 LINE 帳號綁定 |
| `test_line_unbinding` | 測試解除 LINE 綁定 |
| `test_duplicate_line_user_id` | 測試重複 LINE ID 驗證 |
| `test_get_employee_by_line_user_id` | 測試透過 LINE ID 查詢員工 |
| `test_get_employee_data` | 測試取得員工 API 資料格式 |

#### test_hr_attendance_line.py

| 測試方法 | 說明 |
|----------|------|
| `test_clock_in` | 測試上班打卡 |
| `test_clock_out` | 測試下班打卡 |
| `test_duplicate_clock_in` | 測試重複上班打卡驗證 |
| `test_clock_out_without_clock_in` | 測試未打上班卡就打下班卡 |
| `test_get_today_status` | 測試取得今日打卡狀態 |
| `test_get_attendance_history` | 測試取得出勤歷史 |

#### test_line_api.py

| 測試方法 | 說明 |
|----------|------|
| `test_check_binding_not_bound` | 測試檢查綁定 - 未綁定 |
| `test_check_binding_bound` | 測試檢查綁定 - 已綁定 |
| `test_bind_employee_success` | 測試綁定成功 |
| `test_bind_employee_not_found` | 測試綁定 - 找不到員工 |
| `test_clock_in_api` | 測試打卡 API |
| `test_attendance_history_api` | 測試出勤歷史 API |

---

## 變更紀錄

### 2026-01-23
- 升級至 Odoo 19
- 新增 sl_hrm 依賴
- 新增員工搜尋篩選器（已綁定/未綁定 LINE）
- 更新視圖符合 Odoo 19 規範
- 新增完整測試案例
