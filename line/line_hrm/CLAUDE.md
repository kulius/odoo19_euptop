# line_hrm - LINE LIFF 打卡系統前端

## 專案概述

LINE LIFF 打卡系統前端應用，使用 Svelte 5 + Vite 6 + Tailwind CSS 4 開發。

## 技術棧

- **框架**: Svelte 5
- **建置工具**: Vite 6
- **樣式**: Tailwind CSS 4 + DaisyUI 5
- **LINE SDK**: @line/liff 2.24

## 目錄結構

```
line_hrm/
├── package.json
├── vite.config.js
├── index.html
├── src/
│   ├── main.js
│   ├── app.css
│   ├── App.svelte
│   ├── services/
│   │   ├── liff.js          # LINE LIFF SDK 服務
│   │   ├── geolocation.js   # GPS 定位服務
│   │   └── api.js           # Odoo REST API 客戶端
│   ├── stores/
│   │   ├── user.js          # 用戶狀態
│   │   ├── attendance.js    # 出勤狀態
│   │   ├── location.js      # GPS 位置
│   │   └── toast.js         # 通知訊息
│   ├── components/
│   │   ├── Header.svelte
│   │   ├── Toast.svelte
│   │   ├── ClockCard.svelte
│   │   ├── LocationInfo.svelte
│   │   └── BottomMenu.svelte
│   └── pages/
│       ├── BindingPage.svelte
│       └── AttendanceHistory.svelte
└── public/
    └── favicon.svg
```

## 開發指令

```bash
# 安裝依賴
npm install

# 開發模式
npm run dev

# 建置
npm run build

# 預覽建置結果
npm run preview
```

## 環境變數

建立 `.env` 檔案：

```env
VITE_API_BASE_URL=http://localhost:8069
VITE_LIFF_ID=your-liff-id
VITE_USE_MOCK=false
```

## 功能頁面

### 1. 綁定頁面 (BindingPage)
- 顯示 LINE 頭像和名稱
- 輸入公司登記姓名進行綁定

### 2. 打卡頁面 (ClockCard)
- 顯示今日打卡狀態
- GPS 定位
- 上班/下班打卡按鈕

### 3. 出勤歷史 (AttendanceHistory)
- 出勤記錄列表
- 顯示上下班時間和工時

## 後端 API

對應 Odoo 模組：`addons_store/sl_hrm_line`

### API 端點

| 端點 | 方法 | 說明 |
|------|------|------|
| `/api/line/check-binding` | POST | 檢查 LINE 用戶是否已綁定員工 |
| `/api/line/bind` | POST | 綁定 LINE 用戶與員工 |
| `/api/line/user` | GET | 取得用戶資料 |
| `/api/line/attendance/today` | GET | 取得今日出勤狀態 |
| `/api/line/attendance/clock` | POST | 打卡 (上班/下班) |
| `/api/line/attendance/history` | GET | 取得出勤歷史 |

## 部署

### Nginx 設定範例

```nginx
server {
    listen 443 ssl;
    server_name line.your-domain.com;

    root /var/www/line-hrm;
    index index.html;

    location / {
        try_files $uri $uri/ /index.html;
    }

    location /api/line/ {
        proxy_pass http://odoo-server:8069;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

### LINE Developers Console 設定

- **LIFF Endpoint URL**: `https://line.your-domain.com`
- **Scope**: `profile`, `openid`

## 變更紀錄

### 2026-01-23
- 從 Odoo 17 專案複製至 Odoo 19 專案
- 更新 API 基礎網址設定

### 2025-01-16
- 初始建立專案
- 實現 LINE 綁定流程
- 實現 GPS 打卡功能
- 實現出勤歷史查詢
