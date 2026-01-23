# sl_hrm_line - LINE 打卡系統

## 模組概述

LINE LIFF 員工綁定與 GPS 打卡系統，基於 Odoo 17 標準 HR 模組擴展。

## 功能

- **LINE 員工綁定** - 透過員工姓名綁定 LINE 帳號
- **GPS 打卡** - 上下班打卡記錄 GPS 座標（需安裝 hr_attendance 模組）

## 目錄結構

```
sl_hrm_line/
├── __init__.py
├── __manifest__.py
├── models/
│   ├── __init__.py
│   ├── hr_employee.py      # 員工 LINE 綁定欄位
│   └── hr_attendance.py    # GPS 座標欄位（需 hr_attendance）
├── controllers/
│   ├── __init__.py
│   └── line_api.py         # REST API
├── views/
│   ├── hr_employee_views.xml
│   └── hr_attendance_views.xml  # 未載入，需 hr_attendance
└── security/
    └── ir.model.access.csv
```

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

## hr.employee 擴展欄位

```python
line_user_id = fields.Char('LINE User ID', index=True)
line_display_name = fields.Char('LINE 顯示名稱')
line_picture_url = fields.Char('LINE 頭像 URL')
line_binding_date = fields.Datetime('LINE 綁定時間')
is_line_bound = fields.Boolean('已綁定 LINE', compute)
```

## 依賴模組

- `base`
- `hr`
- `hr_attendance` (選用，啟用打卡功能)

## 安裝步驟

1. 將模組放入 Odoo addons 路徑
2. 更新模組列表
3. 搜尋 "LINE 打卡系統" 安裝

## 啟用打卡功能

若要使用 GPS 打卡功能：

1. 安裝 Odoo 標準模組 `hr_attendance`（員工出勤）
2. 修改 `__manifest__.py` 加入依賴：
   ```python
   'depends': ['base', 'hr', 'hr_attendance'],
   ```
3. 修改 `models/__init__.py` 取消註解：
   ```python
   from . import hr_attendance
   ```
4. 修改 `__manifest__.py` data 加入：
   ```python
   'views/hr_attendance_views.xml',
   ```
5. 升級模組

## 前端專案

對應前端：`line_hr_yc/` (Svelte + Vite)

## 變更紀錄

### 2025-01-16
- 初始建立模組
- 從 `yc_hr_line` 改名為 `sl_hrm_line`
- 移除 `hr_attendance` 強制依賴，改為可選
- 新增 API 模組檢查，未安裝 hr_attendance 時回傳友善錯誤
