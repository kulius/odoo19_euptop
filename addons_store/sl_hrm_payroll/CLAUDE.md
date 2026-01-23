# SL HRM Payroll Module (sl_hrm_payroll)

Starry Lord HRM 薪資管理模組 - Odoo 19 薪資計算與管理擴充模組

## 模組概述

此模組為台灣薪資管理系統，提供完整的薪資結構設定、薪資單計算、薪資代扣申報等功能。支援勞健保、勞退、所得稅扣繳等台灣本地化需求。

**版本**: 19.0.1.0.0
**相依**: base, hr, sl_hrm_overtime
**授權**: LGPL-3
**外部依賴**: xlrd (Python)

## 目錄結構

```
sl_hrm_payroll/
├── __init__.py
├── __manifest__.py
├── CLAUDE.md
├── data/                    # 預設資料
│   ├── hr_payroll_data.xml
│   ├── hr_payroll_sequence.xml
│   └── hr_payslip_setting_data.xml
├── models/                  # 主要模型
├── report/                  # 報表定義
├── security/                # 權限設定
├── views/                   # 視圖定義
└── wizard/                  # 精靈對話框
```

## 核心模型

### 薪資結構 (hr.payroll.structure)

**檔案**: `models/hr_payroll_structure.py`

定義薪資計算的結構，包含一組薪資規則。

| 欄位 | 類型 | 說明 |
|------|------|------|
| `name` | Char | 結構名稱 |
| `code` | Char | 參考代碼 |
| `company_id` | Many2one | 所屬公司 |
| `parent_id` | Many2one | 父結構 |
| `rule_ids` | Many2many | 關聯的薪資規則 |
| `auto_recompute_rule_ids` | Many2many | 自動重新計算的薪資項目 |

主要方法：
- `get_all_rules()`: 取得所有適用的薪資規則

---

### 薪資規則 (hr.salary.rule)

**檔案**: `models/hr_salary_rule.py`

定義單一薪資項目的計算邏輯。

| 欄位 | 類型 | 說明 |
|------|------|------|
| `name` | Char | 規則名稱 |
| `code` | Char | 規則代碼 (唯一) |
| `sequence` | Integer | 計算順序 |
| `category_id` | Many2one | 薪資分類 |
| `amount_select` | Selection | 金額計算方式 (fix/percentage/code) |
| `amount_fix` | Float | 固定金額 |
| `amount_percentage` | Float | 百分比 |
| `amount_python_compute` | Text | Python 計算代碼 |
| `condition_select` | Selection | 條件類型 (none/range/python) |
| `baseline` | Selection | 破月計薪方式 |
| `is_basic` | Boolean | 是否為本薪 |
| `is_non_recurring` | Boolean | 非經常性薪資 |
| `is_withholding` | Boolean | 稅費項目 |

破月計薪方式選項：
- `days`: 依實際天數且上限30天
- `month_days`: 依實際天數
- `no_days`: 直接計薪
- `no`: 不計薪
- `healthy`: 健保
- `labor`: 勞保

主要方法：
- `_compute_rule(localdict)`: 計算薪資規則金額

---

### 薪資分類 (hr.salary.rule.category)

**檔案**: `models/hr_salary_rule_category.py`

薪資規則的分類管理。

| 欄位 | 類型 | 說明 |
|------|------|------|
| `name` | Char | 分類名稱 |
| `code` | Char | 分類代碼 |
| `parent_id` | Many2one | 上級分類 |

---

### 薪資單 (hr.payslip)

**檔案**: `models/hr_payslip.py`

員工月薪資單，為模組核心模型。

| 欄位 | 類型 | 說明 |
|------|------|------|
| `name` | Char | 薪資單名稱 |
| `employee_id` | Many2one | 員工 |
| `date_from` | Date | 薪資起算日 |
| `date_to` | Date | 薪資結算日 |
| `salary_date` | Date | 薪資月份 |
| `actual_pay_day` | Date | 發放日期 |
| `payroll_structure_id` | Many2one | 薪資結構 |
| `payslip_line_ids` | One2many | 薪資明細 |
| `payslip_line_other_ids` | One2many | 他項薪資明細 |
| `state` | Selection | 狀態 (draft/confirm/cancel) |
| `all_subtotal` | Float | 實發金額 |
| `payable_add_subtotal` | Float | 應稅加項小計 |
| `computed_salary_tax` | Float | 計算所得稅 |

主要方法：
- `compute_sheet()`: 計算薪資單
- `set_labor_insurance_salary()`: 設定勞保費
- `set_health_insurance_salary()`: 設定健保費
- `set_labor_harm_insurance_salary()`: 設定職災保險費
- `action_generate_pdf()`: 產生 PDF
- `send_mail_report()`: 發送薪資單郵件

---

### 薪資單明細 (hr.payslip.line)

**檔案**: `models/hr_payslip_line.py`

薪資單的各項目明細。

| 欄位 | 類型 | 說明 |
|------|------|------|
| `payslip_id` | Many2one | 所屬薪資單 |
| `salary_rule_id` | Many2one | 薪資規則 |
| `category_id` | Many2one | 分類 |
| `amount` | Integer | 金額 |
| `code` | Char | 代碼 |
| `manual` | Boolean | 手動調整 |
| `note` | Char | 備註 |

---

### 薪資單總表 (sl.hr.payslip.sheet)

**檔案**: `models/hr_payslip_sheet.py`

批次管理薪資單。

| 欄位 | 類型 | 說明 |
|------|------|------|
| `name` | Char | 標題 |
| `company_id` | Many2one | 公司 |
| `salary_date` | Date | 薪資月份 |
| `pay_date` | Date | 發放日期 |
| `date_from` | Date | 薪資起算日 |
| `date_to` | Date | 薪資結算日 |
| `payslip_ids` | One2many | 薪資單列表 |
| `employee_ids` | Many2many | 選擇員工 |
| `state` | Selection | 狀態 |
| `is_salary_sheet` | Boolean | 是否為薪資單 (否則為獎金單) |

主要方法：
- `compute_payslip()`: 批次計算薪資單
- `action_payslip_sheet_done()`: 確認薪資單
- `transfer_to_accounting()`: 傳票作業

---

### 員工薪資設定 (starrylord.employee.payslip.setting)

**檔案**: `models/starrylord_employee_payslip_setting.py`

員工各項薪資規則的金額設定。

| 欄位 | 類型 | 說明 |
|------|------|------|
| `employee_id` | Many2one | 員工 |
| `salary_rule_id` | Many2one | 薪資規則 |
| `start_date` | Date | 開始日期 |
| `change_date` | Date | 異動日期 |
| `change_reason` | Char | 異動原因 |
| `salary_amount` | Float | 薪資金額 |
| `is_basic_wage` | Boolean | 是否為本薪 |

---

### 薪資手動調整 (sl.payroll.adjustment)

**檔案**: `models/sl_payroll_adjustment.py`

薪資手動調整紀錄。

| 欄位 | 類型 | 說明 |
|------|------|------|
| `employee_id` | Many2one | 員工 |
| `payroll_allocation_date` | Date | 認列日期 |
| `salary_rule_id` | Many2one | 薪資規則 |
| `amount` | Float | 金額 |
| `note` | Char | 備註 |
| `exec_status` | Char | 執行狀態 |

---

### 獎金發放紀錄 (sl.bonus.record)

**檔案**: `models/sl_bonus_record.py`

獎金發放管理。

| 欄位 | 類型 | 說明 |
|------|------|------|
| `employee_id` | Many2one | 員工 |
| `payroll_allocation_day` | Date | 認列薪資日期 |
| `actual_pay_day` | Date | 發放日 |
| `amount` | Float | 金額 |
| `salary_rule_id` | Many2one | 薪資規則 |

---

### 薪資代扣申報總表 (payslip.withholding.statement.sheet)

**檔案**: `models/payslip_withholding_statement_sheet.py`

年度薪資代扣申報管理。

| 欄位 | 類型 | 說明 |
|------|------|------|
| `apply_year` | Date | 申報年度 |
| `date_from` | Date | 申報起算日 |
| `date_to` | Date | 申報結算日 |
| `statement_ids` | One2many | 申報表紀錄 |

主要方法：
- `general_statement()`: 生成申報表紀錄
- `download_excel()`: 下載 Excel 格式
- `download_csv()`: 下載 CSV 格式
- `download_txt()`: 下載 TXT 格式

---

### 中介模型

| 模型 | 說明 | 檔案 |
|------|------|------|
| `starrylord.payslip.holiday.middleware` | 請假明細 | `starrylord_payslip_holiday_middleware.py` |
| `starrylord.payslip.overtime.middleware` | 加班明細 | `starrylord_payslip_overtime_middleware.py` |
| `starrylord.payslip.overtime.holiday.middleware` | 加班補休明細 | `starrylord_payslip_overtime_holiday_middleware.py` |
| `starrylord.employee.payslip.salary.setting` | 本薪變化 | `starrylord_employee_payslip_salary_setting.py` |

---

## 員工擴充 (hr.employee.base)

**檔案**: `models/hr_employee.py`

擴充員工模型，新增薪資相關欄位：

| 欄位 | 類型 | 說明 |
|------|------|------|
| `payroll_structure_id` | Many2one | 薪資結構 |
| `payslip_setting_ids` | One2many | 薪資設定 |
| `is_payslip_compute` | Boolean | 正在計算薪資中 |

主要方法：
- `action_generate_salary_rules()`: 根據薪資結構生成薪資規則設定

---

## 精靈 (Wizard)

| 模型 | 說明 | 檔案 |
|------|------|------|
| `wizard.payslip.salary.rule.add` | 新增薪資項目 | `wizard_payslip_salary_rule_add.py` |
| `wizard.payslip.line.edit` | 變更薪資規則 | `wizard_payslip_line_edit.py` |
| `payslip.sheet.report.wizard` | 薪資總表報表精靈 | `payslip_sheet_report_wizard.py` |
| `payslip.withholding.statement.wizard` | 代扣申報精靈 | `payslip_withholding_statement_wizard.py` |

---

## 報表

| 報表 | 說明 |
|------|------|
| `action_report_hr_payslip` | 薪資單 PDF 報表 |
| `payslip_sheet_report_template` | 薪資總表報表 |
| `payslip_bonus_sheet_report_template` | 獎金總表報表 |
| `payslip_withholding_statement_template` | 代扣申報報表 |

---

## 權限群組

| 群組 ID | 名稱 | 說明 |
|---------|------|------|
| `group_sl_hrm_payroll` | 一般員工薪資單 | 可查看薪資單，無法編輯 |
| `group_sl_hrm_payroll_manager` | 薪資單管理 | 完整薪資管理權限 |

---

## 系統設定

**模型**: `res.config.settings`
**檔案**: `models/res_config_settings.py`

| 設定參數 | 說明 |
|----------|------|
| `sl_hrm_payroll.tax_baseline_amount` | 扣繳 5% 薪資金額門檻 |
| `sl_hrm_payroll.regular_holiday_exclude_payroll` | 薪資計算排除例假日 |

---

## 薪資計算流程

1. **建立薪資單總表** (`sl.hr.payslip.sheet`)
   - 設定薪資月份、起迄日期、發放日期
   - 選擇員工 (或自動選取)

2. **批次計算** (`compute_payslip`)
   - 為每位員工建立薪資單
   - 根據薪資結構取得所有規則
   - 依序計算各薪資項目

3. **薪資規則計算** (`_compute_rule`)
   - 固定金額: 直接套用設定值
   - 百分比: 根據基數計算
   - Python 代碼: 執行自訂邏輯

4. **破月計算**
   - 根據 `baseline` 設定計算在職比例
   - 調整各項目金額

5. **確認發放** (`action_payslip_sheet_done`)
   - 變更狀態為已確認
   - 可產生 PDF 並發送郵件

---

## 開發注意事項

1. **薪資規則代碼唯一性**: 每個公司內的薪資規則代碼 (`code`) 必須唯一

2. **PyPDF2 版本**: 使用新版 API (`PdfWriter`, `PdfReader`)

3. **safe_eval**: 薪資規則的 Python 代碼使用 `safe_eval` 執行，確保安全性

4. **計算順序**: 薪資規則依 `sequence` 欄位排序計算，注意依賴關係

5. **破月計算**: 員工入離職時需正確計算在職天數比例

---

## 視圖入口

主選單路徑: Starry Lord HRM → 薪資管理

- 薪資結構
- 薪資規則
- 薪資分類
- 薪資單總表
- 獎金管理
- 薪資調整
- 代扣申報

---

## 升級/安裝問題記錄

> **注意**: Odoo 19 通用升級問題請參考根目錄 `CLAUDE.md`

### 本模組修復記錄 (2026-01-12)

| 問題 | 檔案 | 修復內容 |
|------|------|----------|
| PyPDF2 API 變更 | `models/hr_payslip.py` | `PdfFileWriter/Reader` → `PdfWriter/Reader` |
| name_get 已棄用 | `models/starrylord_employee_payslip_salary_setting.py` | 改用 `_compute_display_name()` |
| wizard 未 import | `wizard/__init__.py` | 加入 `wizard_payslip_batch_process`, `wizard_payslip_sheet_select_employee` |
| wizard 權限缺失 | `security/ir.model.access.csv` | 加入 `hr.payslip.batch.processing`, `wizard.payslip.select.employee` 權限 |
| wizard XML 未聲明 | `__manifest__.py` | 加入 `wizard/hr_payslip_batch_processing.xml` |

### 本模組修復記錄 (2026-01-13)

| 問題 | 檔案 | 修復內容 |
|------|------|----------|
| comodel_name 錯誤 | `models/sl_payroll_adjustment.py` | `hr.payslip.sheet` → `sl.hr.payslip.sheet` |
| Many2many 關聯表衝突 | `wizard/wizard_payslip_sheet_select_employee.py` | 使用 `wizard_payslip_select_employee_rel` |
| Many2many 關聯表衝突 | `wizard/wizard_payslip_batch_process.py` | 使用 `hr_payslip_batch_processing_employee_rel` |
| 報表缺少 _description | `report/report_hr_payslip.py` | 新增 `_description = '薪資單報表'` |
| Search View 無效屬性 | `views/hr_salary_rule.xml` | 移除 `group` 元素的 `col`, `colspan`, `expand`, `string` 屬性 |

### 本模組修復記錄 (2026-01-23)

| 問題 | 檔案 | 修復內容 |
|------|------|----------|
| 依賴模組合併 | `__manifest__.py` | `sl_hrm_overtime` → `sl_hrm` (因 sl_hrm_overtime 已合併至 sl_hrm) |
| 版本更新 | `__manifest__.py` | `19.0.1.0.0` → `19.0.1.1.0` |
| 權限整理 | `security/sl_hrm_payroll_security.xml` | 使用 `res.groups.privilege` 在「人力資源」分類下新增「薪資」目錄 |
| 資料遷移驗證 | 測試資料 | 從 odoo17_yc_hrtest 遷移測試資料至 odoo19_sanoc |
| 重複薪資規則 | 資料清理 | 移除重複的 salary rules (85 → 43 條) |
| 員工薪資設定 ID 對應 | 資料遷移 | 正確對應 salary_rule_id 從 Odoo 17 到 Odoo 19 |

---

## Odoo 17 vs Odoo 19 檔案比對結果

此模組已完成從 Odoo 17 到 Odoo 19 的升級，以下為檔案比對結果：

| 類別 | 檔案數量 | 狀態 |
|------|----------|------|
| Models | 22 | ✅ 完整 |
| Views | 14 | ✅ 完整 |
| Wizard | 11 | ✅ 完整 |
| Security | 2 | ✅ 完整 |
| Report | 8 | ✅ 完整 |
| Data | 3 | ✅ 完整 |

### Models (22 檔案)

所有模型檔案皆已遷移：
- `hr_employee.py` - 員工擴充
- `hr_payroll_structure.py` - 薪資結構
- `hr_payslip.py` - 薪資單
- `hr_payslip_line.py` - 薪資單明細
- `hr_payslip_line_other.py` - 其他薪資明細
- `hr_payslip_sheet.py` - 薪資單總表
- `hr_salary_rule.py` - 薪資規則
- `hr_salary_rule_category.py` - 薪資分類
- `payslip_withholding_statement.py` - 代扣申報
- `payslip_withholding_statement_sheet.py` - 代扣申報總表
- `res_config_settings.py` - 系統設定
- `sl_bonus_record.py` - 獎金紀錄
- `sl_payroll_adjustment.py` - 薪資調整
- `starrylord_employee_payslip_salary_setting.py` - 本薪設定
- `starrylord_employee_payslip_setting.py` - 員工薪資設定
- `starrylord_payslip_holiday_middleware.py` - 請假中介
- `starrylord_payslip_overtime_holiday_middleware.py` - 加班補休中介
- `starrylord_payslip_overtime_middleware.py` - 加班中介

### Views (14 檔案)

所有視圖檔案皆已遷移並升級為 Odoo 19 語法：
- `hr_employee_view.xml`
- `hr_payroll_structure.xml`
- `hr_payslip.xml`
- `hr_payslip_sheet.xml`
- `hr_salary_rule.xml`
- `hr_salary_rule_category.xml`
- `menu.xml`
- `payslip_withholding_statement_sheet.xml`
- `res_config_settings.xml`
- `sl_bonus_record_view.xml`
- `sl_payroll_adjustment.xml`
- `starrylord_employee_payslip_salary_setting.xml`
- `starrylord_employee_payslip_setting.xml`

### Wizard (11 檔案)

所有精靈檔案皆已遷移：
- `hr_payslip_batch_processing.py` / `.xml`
- `payslip_sheet_report_wizard.py` / `.xml`
- `payslip_withholding_statement_wizard.py` / `.xml`
- `wizard_payslip_line_edit.py` / `.xml`
- `wizard_payslip_salary_rule_add.py` / `.xml`
- `wizard_payslip_sheet_select_employee.py` / `.xml`

### Report (8 檔案)

所有報表檔案皆已遷移：
- `report_hr_payslip.py`
- `report_hr_payslip.xml`
- `report_hr_payslip_template.xml`
- `report_payslip_sheet.xml`
- `report_payslip_sheet_template.xml`
- `report_payslip_withholding_statement.xml`
- `report_payslip_withholding_statement_template.xml`

---

## 權限結構

Odoo 19 使用 `res.groups.privilege` 來組織權限分類：

```
人力資源 (base.module_category_human_resources)
├── 員工 (hr.res_groups_privilege_employees)
├── 考勤 (hr_attendance.res_groups_privilege_attendances)
└── 薪資 (sl_hrm_payroll.res_groups_privilege_payroll)  ← 本模組新增
    ├── 使用者 (group_sl_hrm_payroll)
    └── 管理員 (group_sl_hrm_payroll_manager)
```
