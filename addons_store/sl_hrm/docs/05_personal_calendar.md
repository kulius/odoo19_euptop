# 個人行事曆與排班 (Personal Calendar & Schedule)

本文件說明 sl_hrm 模組的個人行事曆與排班管理功能。

> **來源**: 原 `sl_hrm_personal_calendar` 模組，已合併至 `sl_hrm`

---

## 模型結構

### 排班 (hr.schedule)

**檔案**: `models/hr_schedule.py`

定義員工的固定排班樣板。

| 欄位 | 說明 |
|------|------|
| `name` | 排班名稱 |
| `employee_ids` | 適用員工 |
| `schedule_line_ids` | 排班明細 |
| `is_active` | 是否啟用 |

---

### 排班時段類型 (hr.schedule.time.type)

**檔案**: `models/hr_schedule_time_type.py`

定義排班的時段類型。

| 欄位 | 說明 |
|------|------|
| `name` | 類型名稱 |
| `code` | 代碼 |
| `color` | 顯示顏色 |

常見類型:
- 正常上班
- 加班
- 休息
- 假日

---

### 時間列表 (starrylord.time.list)

**檔案**: `models/starrylord_time_list.py`

時間選項列表，用於排班設定。

| 欄位 | 說明 |
|------|------|
| `name` | 顯示名稱 |
| `hour` | 小時 |
| `minute` | 分鐘 |

---

### 個人行事曆 (hr.personal.calendar)

**檔案**: `models/hr_personal_calendar.py`

員工的每日行事曆記錄，整合排班、請假、加班資訊。

| 欄位 | 說明 |
|------|------|
| `employee_id` | 員工 |
| `calendar_date` | 日期 |
| `schedule_id` | 排班 |
| `time_type_id` | 時段類型 |
| `start_time` | 開始時間 |
| `end_time` | 結束時間 |
| `holiday_apply_id` | 關聯請假單 |
| `overtime_apply_id` | 關聯加班單 |
| `is_holiday` | 是否為假日 |
| `note` | 備註 |

---

## 行事曆產生邏輯

### 從排班產生

系統可依據排班樣板自動產生未來期間的個人行事曆。

### 從請假單產生

請假單核准後，自動產生對應日期的行事曆記錄，標記為請假。

### 從加班單產生

加班單核准後，自動產生對應日期的行事曆記錄，標記為加班。

---

## 選單結構

```
Starry Lord HRM
└── 個人行事曆
    ├── 我的行事曆 (hr.personal.calendar)
    ├── 行事曆管理
    └── 設定
        ├── 排班樣板
        ├── 時段類型
        └── 時間列表
```

---

## 視圖檔案

| 檔案 | 說明 |
|------|------|
| `views/hr_personal_calendar.xml` | 個人行事曆視圖 |
| `views/hr_schedule.xml` | 排班視圖 |
| `views/hr_schedule_time_type.xml` | 時段類型視圖 |
| `views/starrylord_time_list.xml` | 時間列表視圖 |

---

## 整合說明

### 與考勤整合

考勤核對時參照個人行事曆，判斷員工當日應出勤時段。

### 與請假整合

請假核准後自動產生行事曆記錄，考勤核對時可識別請假時段。

### 與加班整合

加班核准後自動產生行事曆記錄，考勤核對時可識別加班時段。

### 與國定假日整合

系統支援設定國定假日 (`hr.public.holiday`)，行事曆產生時會標記。
