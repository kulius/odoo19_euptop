# 核心人資功能 (Core HR)

本文件說明 sl_hrm 模組的核心人資管理功能。

## 員工管理 (hr.employee 擴充)

**檔案**: `models/hr_employee.py`

### 主要擴充欄位

| 欄位 | 類型 | 說明 |
|------|------|------|
| `employee_number` | Char | 員工編號 (自動產生) |
| `state` | Selection | 狀態: draft/working/resign |
| `registration_date` | Date | 入職日期 |
| `resignation_date` | Date | 離職日期 |
| `job_tenure` | Char | 工作年資 (計算欄位) |
| `is_foreign` | Boolean | 外籍員工 |
| `is_no_need_check_in` | Boolean | 無需打卡 |
| `gender` | Selection | 性別 (Odoo 19 自行定義) |

### 員工編號產生規則

```
格式: {公司前綴}{年份(2碼)}{流水號(3碼)}
範例: A25001 (A公司, 2025年, 第1位)
```

程式碼位置: `models/hr_employee.py:314-347`

### 員工狀態計算邏輯

依據 `hr_employee_working_ids` 最新異動記錄決定狀態:
- `on_board/reinstatement/furlough` → `working`
- `resign` → `resign`
- 無記錄 → `draft`

---

## 在離職異動

**模型**: `hr.employee.working`
**檔案**: `models/hr_employee_working.py`

記錄員工到職、離職、留職停薪、復職等異動歷程。

### 異動原因選項

| 代碼 | 說明 |
|------|------|
| `on_board` | 到職 |
| `resign` | 離職 |
| `furlough` | 留職停薪 |
| `reinstatement` | 復職 |

### 異動限制

- 必須先離職才能再到職
- 異動有邏輯檢查防止不合理操作

---

## 保險級距系統

### 級距模型

| 模型 | 說明 | 檔案 |
|------|------|------|
| `hr.labor.insurance.gap` | 勞保級距 | `hr_labor_insurance_gap.py` |
| `hr.health.insurance.gap` | 健保級距 | `hr_health_insurance_gap.py` |
| `hr.labor.pension.gap` | 勞退級距 | `hr_labor_pension_gap.py` |
| `hr.labor.harm.insurance.gap` | 職災保險級距 | `hr_labor_harm_insurance_gap.py` |
| `hr.salary.tax.gap` | 薪資所得稅級距 | `hr_salary_tax_gap.py` |

### 保險異動歷程

| 模型 | 說明 | 檔案 |
|------|------|------|
| `hr.labor.insurance.history` | 勞保異動歷程 | `hr_labor_insurance_history.py` |
| `hr.health.insurance.history` | 健保異動歷程 | `hr_health_insurance_history.py` |
| `hr.labor.pension.history` | 勞退異動歷程 | `hr_labor_pension_history.py` |
| `hr.labor.harm.insurance.history` | 職災保險異動 | `hr_labor_harm_insurance_history.py` |

### 異動原因選項

| 代碼 | 說明 |
|------|------|
| `add` | 加保 |
| `off` | 退保 |
| `promote` | 調薪 |

### 保險級距自動更新

員工保險級距欄位為計算欄位，依據各保險異動歷程中最新生效的記錄自動更新。

---

## 眷保資料

**模型**: `hr.dependents.information`
**檔案**: `models/hr_dependents_information.py`

管理員工眷屬健保資料，包含台灣身分證格式驗證邏輯。

---

## 體檢與證照管理

| 模型 | 說明 |
|------|------|
| `sl.health.report.line` | 體檢報告明細 |
| `sl.health.report.check.setting` | 體檢有效期設定 (依年齡區間) |
| `sl.hr.license.line` | 證照明細 |
| `sl.license.check.setting` | 證照有效期設定 |

---

## 其他模型

| 模型 | 說明 |
|------|------|
| `sl.plant.area` | 廠區管理 |
| `sl.hr.insurance.doc` | 保險文件 |
| `starrylord.hr.emergency.contact` | 緊急聯絡人 |

---

## 自動化任務

**檔案**: `job/sl_hr_auto_job.py`
**模型**: `sl.hr.auto.job`

| 方法 | 說明 |
|------|------|
| `job_run()` | 離職員工自動停用帳號 |
| `job_auto_create_on_board_user()` | 到職日自動建立使用者帳號 |

---

## 批次操作

**模型**: `hr.batch.operation`
**檔案**: `models/hr_batch_operation.py`

| 方法 | 說明 |
|------|------|
| `action_update_all_labor_current_year_insurance_interval()` | 更新所有員工當年勞健保級距 |

---

## 破月計算

| 方法 | 說明 |
|------|------|
| `is_partial_month()` | 判斷是否為破月 |
| `get_partial_month_ratio()` | 計算破月在職比例 |

---

## 相關精靈

| 精靈 | 檔案 |
|------|------|
| 眷保新增精靈 | `wizard/wizard_dependents_add.xml` |
| 勞保異動精靈 | `wizard/wizard_labor_insurance_change.xml` |
| 健保異動精靈 | `wizard/wizard_health_insurance_change.xml` |
| 勞退異動精靈 | `wizard/wizard_labor_pension_change.xml` |
| 職災保險異動精靈 | `wizard/wizard_labor_harm_insurance_change.xml` |

---

## 開發注意事項

1. **附件公開設定**: 所有 `ir.attachment` 相關欄位在 create/write 時會自動設為 `public = True`

2. **身分證驗證**: `hr.dependents.information` 模型包含台灣身分證格式驗證

3. **政府補助設定**: 勞健保異動歷程包含政府補助比例設定

4. **gender 欄位**: Odoo 19 移除了 hr.employee 的 gender 欄位，本模組自行定義
