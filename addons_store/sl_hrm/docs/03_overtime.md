# 加班管理 (Overtime)

本文件說明 sl_hrm 模組的加班管理功能。

> **來源**: 原 `sl_hrm_overtime` 模組，已合併至 `sl_hrm`

---

## 模型結構

### 加班類型 (starrylord.overtime.type)

**檔案**: `models/starrylord_overtime_type.py`

定義系統支援的加班類型。

| 欄位 | 說明 |
|------|------|
| `name` | 類型名稱 |
| `time_type` | 計算單位 (day/hour) |
| `code` | 類型代碼 |

---

### 加班單 (starrylord.overtime.apply)

**檔案**: `models/starrylord_overtime_apply.py`

員工加班申請單，整合簽核流程。

#### 主要欄位

| 欄位 | 說明 |
|------|------|
| `name` | 單號 (自動產生) |
| `employee_id` | 申請人 |
| `overtime_type_id` | 加班類型 |
| `start_day` | 起始日期 |
| `end_day` | 結束日期 |
| `apply_from` | 起始時間 |
| `apply_to` | 結束時間 |
| `overtime_time_total` | 加班時數 |
| `state` | 狀態 |

#### 狀態流程

```
draft → f_approve → agree
              ↓
           refused
```

| 狀態 | 說明 |
|------|------|
| `draft` | 草稿 |
| `f_approve` | 送簽中 |
| `agree` | 已核准 |
| `refused` | 已駁回 |

---

### 加班時數級距 (starrylord.overtime.tier.definition)

**檔案**: `models/starrylord_overtime_tier_definition.py`

定義加班時數的計算級距（如前2小時1.34倍，之後1.67倍）。

| 欄位 | 說明 |
|------|------|
| `overtime_type_id` | 加班類型 |
| `hour_from` | 起始小時 |
| `hour_to` | 結束小時 |
| `multiplier` | 倍率 |

---

### 補休換取同意書 (overtime.exchange.consent)

**檔案**: `models/overtime_exchange_consent.py`

記錄員工同意將加班時數換取補休的同意書。

| 欄位 | 說明 |
|------|------|
| `employee_id` | 員工 |
| `consent_date` | 同意日期 |
| `overtime_apply_ids` | 關聯加班單 |

---

## 系統參數

加班管理功能使用以下系統參數:

| 參數名稱 | 說明 |
|----------|------|
| `sl_hrm_overtime.max_overtime_month` | 單月加班上限 |
| `sl_hrm_overtime.max_overtime_three_month` | 三個月加班上限 |
| `sl_hrm_overtime.single_month_limit` | 單月延長上限 |
| `sl_hrm_overtime.total_month_limit` | 總月延長上限 |

---

## 選單結構

```
Starry Lord HRM
└── 加班
    ├── 我的加班單 (action: starrylord_overtime_apply_action)
    ├── 加班單審核 (action: action_overtime_apply_portal_todo)
    ├── 加班管理 (action: starrylord_overtime_apply_manager_action)
    ├── 補休換取
    │   └── 補休換取同意書
    └── 設定
        ├── 加班類型
        └── 加班時數級距
```

---

## 視圖檔案

| 檔案 | 說明 |
|------|------|
| `views/starrylord_overtime_apply.xml` | 加班單視圖 |
| `views/starrylord_overtime_type.xml` | 加班類型視圖 |
| `views/starrylord_overtime_settings.xml` | 加班設定視圖 |
| `views/overtime_exchange_consent_views.xml` | 補休換取同意書視圖 |
| `views/starrylord_overtime_menu.xml` | 加班選單 |

---

## 報表

| 檔案 | 說明 |
|------|------|
| `report/overtime_exchange_consent_templates.xml` | 補休換取同意書列印範本 |

---

## 安全群組

| 群組 ID | 說明 |
|---------|------|
| `group_starrylord_overtime_developer` | 加班開發者 |
| `group_starrylord_overtime_manager` | 加班管理員 |
| `group_starrylord_overtime_director` | 加班主管 |

群組繼承關係: `director` → `manager` → `developer`

---

## 整合說明

### 與補休整合

加班核准後，可依設定自動產生補休配額 (`starrylord.holiday.allocation`)。

### 與簽核整合

加班單繼承 `tier.validation` mixin，支援多層簽核流程。

### 與考勤整合

加班單核准後，會產生對應的個人行事曆記錄 (`hr.personal.calendar`)，用於考勤比對。
