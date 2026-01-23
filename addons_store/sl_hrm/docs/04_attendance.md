# 考勤管理 (Attendance)

本文件說明 sl_hrm 模組的考勤管理功能。

> **來源**: 原 `sl_hr_attendance` 模組，已合併至 `sl_hrm`

---

## 模型結構

### 原始打卡資料 (starrylord.hr.attendance.raw)

**檔案**: `models/starrylord_hr_attendance_raw.py`

從打卡設備匯入的原始打卡資料。

| 欄位 | 說明 |
|------|------|
| `employee_id` | 員工 |
| `punch_time` | 打卡時間 |
| `punch_type` | 打卡類型 (in/out) |
| `device_id` | 設備 ID |
| `source` | 資料來源 |

---

### 考勤記錄 (hr.attendance 擴充)

**檔案**: `models/starrylord_hr_attendance.py`

擴充 Odoo 原生考勤記錄。

| 擴充欄位 | 說明 |
|----------|------|
| `employee_number` | 員工編號 (related) |
| `employee_department_id` | 部門 (related) |
| `is_manual` | 是否手動調整 |
| `adjusted_by` | 調整人 |

---

### 考勤核對 (starrylord.hr.attendance.check)

**檔案**: `models/starrylord_hr_attendance_check.py`

比對打卡記錄與排班/請假/加班的差異。

| 欄位 | 說明 |
|------|------|
| `employee_id` | 員工 |
| `check_date` | 核對日期 |
| `schedule_id` | 排班 |
| `check_in` | 實際上班打卡 |
| `check_out` | 實際下班打卡 |
| `status` | 狀態 (normal/late/early/absent) |
| `late_minutes` | 遲到分鐘數 |
| `early_minutes` | 早退分鐘數 |

---

### 補打卡申請 (sl.attendance.repair)

**檔案**: `models/sl_attendance_repair.py`

員工補打卡申請單，整合簽核流程。

| 欄位 | 說明 |
|------|------|
| `name` | 單號 |
| `employee_id` | 申請人 |
| `repair_date` | 補卡日期 |
| `repair_time` | 補卡時間 |
| `repair_type` | 補卡類型 (in/out) |
| `reason` | 補卡原因 |
| `state` | 狀態 |

---

## 匯入功能

### 考勤匯入精靈 (sl.attendance.import)

**檔案**: `wizard/sl_attendance_import.py`

支援從 Excel 檔案匯入打卡資料。

| 欄位 | 說明 |
|------|------|
| `file` | 上傳檔案 |
| `filename` | 檔案名稱 |

**支援格式**: Excel (.xlsx, .xls)

**外部依賴**: `pandas`, `openpyxl`

---

## 核對精靈

### 考勤核對精靈 (wizard.hr.attendance.check)

**檔案**: `wizard/wizard_hr_attendance_check.py`

批次執行考勤核對。

| 欄位 | 說明 |
|------|------|
| `date_from` | 起始日期 |
| `date_to` | 結束日期 |
| `employee_ids` | 員工 (可選多筆) |

---

## 選單結構

```
Starry Lord HRM
└── 考勤
    ├── 打卡記錄 (hr.attendance)
    ├── 原始打卡資料 (starrylord.hr.attendance.raw)
    ├── 考勤核對 (starrylord.hr.attendance.check)
    ├── 補打卡申請 (sl.attendance.repair)
    └── 匯入
        └── 考勤匯入
```

---

## 視圖檔案

| 檔案 | 說明 |
|------|------|
| `views/hr_attendance_view.xml` | 考勤記錄視圖 |
| `views/hr_attendance_raw_view.xml` | 原始打卡資料視圖 |
| `views/sl_attendance_repair.xml` | 補打卡申請視圖 |
| `views/sl_attendance_import_view.xml` | 匯入視圖 |
| `views/menu_inherit.xml` | 考勤選單 |

---

## 安全群組

考勤功能使用 `hr_attendance` 模組的群組:

| 群組 | 說明 |
|------|------|
| `hr_attendance.group_hr_attendance_user` | 考勤使用者 |
| `hr_attendance.group_hr_attendance_manager` | 考勤管理員 |

---

## 異常通知

### Email 範本

**檔案**: `data/email_template_attendance_anomaly.xml`

考勤異常時發送通知郵件給主管。

---

## 整合說明

### 與請假整合

考勤核對時會比對請假記錄，判斷缺勤是否為請假。

### 與加班整合

考勤核對時會比對加班記錄，計算實際加班時數。

### 與排班整合

考勤核對依據排班時間判斷遲到、早退。

### 與簽核整合

補打卡申請繼承 `tier.validation` mixin，支援多層簽核流程。
