# 請休假管理 (Holiday)

本文件說明 sl_hrm 模組的請休假管理功能。

> **來源**: 原 `sl_hrm_holiday` 模組，已合併至 `sl_hrm`

---

## 模型結構

### 假別類型 (starrylord.holiday.type)

**檔案**: `models/starrylord_holiday_type.py`

定義系統支援的假別，如特休、病假、事假、生理假、補休等。

| 欄位 | 說明 |
|------|------|
| `name` | 假別名稱 |
| `time_type` | 計算單位 (day/hour) |
| `is_annual` | 是否為特休 |
| `is_sick` | 是否為病假 |

---

### 假別配額 (starrylord.holiday.allocation)

**檔案**: `models/starrylord_holiday_allocation.py`

管理員工各假別的年度配額。

| 欄位 | 說明 |
|------|------|
| `employee_id` | 員工 |
| `holiday_type_id` | 假別類型 |
| `total_time` | 總配額 (小時) |
| `used_time` | 已使用 (小時) |
| `last_time` | 剩餘 (小時) |
| `validity_start` | 生效起日 |
| `validity_end` | 生效迄日 |

---

### 請假單 (starrylord.holiday.apply)

**檔案**: `models/starrylord_holiday_apply.py`

員工請假申請單，整合簽核流程。

#### 主要欄位

| 欄位 | 說明 |
|------|------|
| `name` | 單號 (自動產生) |
| `employee_id` | 申請人 |
| `holiday_allocation_id` | 使用配額 |
| `start_day` | 起始日期 |
| `end_day` | 結束日期 |
| `apply_from` | 起始時間 |
| `apply_to` | 結束時間 |
| `holiday_time_total` | 請假時數 |
| `substitute_id` | 職務代理人 |
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

#### 出勤檢核欄位 (HR 作業用)

| 欄位 | 說明 |
|------|------|
| `leave_attendance_check_state` | 檢核狀態 (pending/ok/ng) |
| `leave_attendance_process_state` | 處理狀態 (pending/done) |
| `leave_attendance_abnormal_reason` | 異常說明 |
| `cancel_ids` | 關聯銷假單 |

---

### 銷假單 (starrylord.holiday.cancel)

**檔案**: `models/starrylord_holiday_cancel.py`

處理請假後因出勤異常需銷假的情況。

| 欄位 | 說明 |
|------|------|
| `holiday_apply_id` | 關聯請假單 |
| `cancel_day` | 銷假日期 |
| `cancel_hours` | 銷假時數 |
| `state` | 狀態 |

---

### 使用紀錄 (starrylord.holiday.used.record)

**檔案**: `models/starrylord_holiday_used_record.py`

記錄假別配額的使用明細，包含銷假沖銷。

| 欄位 | 說明 |
|------|------|
| `holiday_allocation_id` | 配額 |
| `holiday_apply_id` | 請假單 |
| `holiday_day` | 日期 |
| `hours` | 時數 (負數表示沖銷) |
| `note` | 備註 |

---

## 系統參數

請休假功能使用以下系統參數 (`ir.config_parameter`):

| 參數名稱 | 說明 |
|----------|------|
| `sl_hrm_holiday.holiday_special_id` | 特休假別 ID |
| `sl_hrm_holiday.holiday_sick_id` | 病假假別 ID |
| `sl_hrm_holiday.holiday_leave_id` | 事假假別 ID |
| `sl_hrm_holiday.holiday_menstrual_id` | 生理假假別 ID |
| `sl_hrm_holiday.holiday_comp_id` | 補休假別 ID |

---

## Dashboard API

### retrieve_dashboard()

**位置**: `models/starrylord_holiday_apply.py:825`

提供 OWL Dashboard 所需資料。

**回傳格式**:

```python
{
    'annual_leave_hours': 0,      # 特休剩餘
    'sick_leave_hours': 0,        # 病假剩餘
    'compensation_leave_hours': 0, # 補休剩餘
    'private_leave_hours': 0,     # 事假剩餘
    'menstrual_leave_hours': 0,   # 生理假剩餘
    'gender': 'male/female/other' # 員工性別
}
```

---

## 選單結構

```
Starry Lord HRM
└── 請休假
    ├── 我的假單 (action: starrylord_holiday_apply_action)
    ├── 請假單審核 (action: action_holiday_apply_portal_todo)
    ├── 休假管理 (action: starrylord_holiday_apply_manager_action)
    ├── 假別設定
    │   ├── 假別配額
    │   ├── 假別類型
    │   └── 特休設定
    └── 設定
        ├── 小時選項
        └── 分鐘選項
```

---

## 視圖檔案

| 檔案 | 說明 |
|------|------|
| `views/starrylord_holiday_apply.xml` | 請假單視圖 |
| `views/starrylord_holiday_allocation.xml` | 配額視圖 |
| `views/starrylord_holiday_type.xml` | 假別類型視圖 |
| `views/starrylord_holiday_cancel.xml` | 銷假單視圖 |
| `views/starrylord_holiday_used_record.xml` | 使用紀錄視圖 |
| `views/starrylord_holiday_menu.xml` | 請休假選單 |

---

## 安全群組

| 群組 ID | 說明 |
|---------|------|
| `group_starrylord_holiday_developer` | 請休假開發者 |
| `group_starrylord_holiday_manager` | 請休假管理員 |
| `group_starrylord_holiday_director` | 請休假主管 |

群組繼承關係: `director` → `manager` → `developer`

---

## 整合說明

### 與考勤整合

請假單核准後，會產生對應的個人行事曆記錄 (`hr.personal.calendar`)，用於考勤比對。

### 與簽核整合

請假單繼承 `tier.validation` mixin，支援多層簽核流程。
