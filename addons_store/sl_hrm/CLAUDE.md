# SL HRM Module (sl_hrm)

Starry Lord HRM 人資管理模組 - Odoo 19 人力資源管理擴充模組

## 模組概述

此模組為台灣人力資源管理系統，擴充 Odoo 原生 HR 模組，提供台灣勞健保、勞退、職災保險管理功能。

**版本**: 19.0.1.0.0
**相依**: base, hr, hr_skills
**授權**: LGPL-3

## 目錄結構

```
sl_hrm/
├── __init__.py
├── __manifest__.py
├── data/               # 序號資料 (員工編號)
├── job/                # 自動化排程任務
├── models/             # 主要模型
├── security/           # 權限設定
├── views/              # 視圖定義
└── wizard/             # 精靈對話框
```

## 核心模型

### 員工相關 (hr.employee 擴充)

**檔案**: `models/hr_employee.py`

主要擴充欄位：
- `employee_number`: 員工編號 (自動產生，格式: 前綴+年份+流水號)
- `state`: 狀態 (draft/working/resign)
- `registration_date`: 入職日期
- `resignation_date`: 離職日期
- `job_tenure`: 工作年資 (計算欄位)
- `is_foreign`: 外籍員工
- `is_no_need_check_in`: 無需打卡

### 在離職異動

**模型**: `hr.employee.working`
**檔案**: `models/hr_employee_working.py`

記錄員工到職、離職、留職停薪、復職等異動歷程。

異動原因選項:
- `on_board`: 到職
- `resign`: 離職
- `furlough`: 留職停薪
- `reinstatement`: 復職

### 保險級距系統

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

異動原因選項:
- `add`: 加保
- `off`: 退保
- `promote`: 調薪

### 眷保資料

**模型**: `hr.dependents.information`
**檔案**: `models/hr_dependents_information.py`

管理員工眷屬健保資料，包含身分證驗證邏輯 (台灣身分證格式)。

### 體檢與證照管理

| 模型 | 說明 |
|------|------|
| `sl.health.report.line` | 體檢報告明細 |
| `sl.health.report.check.setting` | 體檢有效期設定 (依年齡區間) |
| `sl.hr.license.line` | 證照明細 |
| `sl.license.check.setting` | 證照有效期設定 |

### 其他模型

| 模型 | 說明 |
|------|------|
| `sl.plant.area` | 廠區管理 |
| `sl.hr.insurance.doc` | 保險文件 |
| `starrylord.hr.emergency.contact` | 緊急聯絡人 |

## 自動化任務

**檔案**: `job/sl_hr_auto_job.py`
**模型**: `sl.hr.auto.job`

- `job_run()`: 離職員工自動停用帳號
- `job_auto_create_on_board_user()`: 到職日自動建立使用者帳號

## 批次操作

**模型**: `hr.batch.operation`
**檔案**: `models/hr_batch_operation.py`

- `action_update_all_labor_current_year_insurance_interval()`: 更新所有員工當年勞健保級距

## 重要邏輯

### 員工編號產生規則

```
格式: {公司前綴}{年份(2碼)}{流水號(3碼)}
範例: A25001 (A公司, 2025年, 第1位)
```

程式碼位置: `models/hr_employee.py:314-347`

### 員工狀態計算

依據 `hr_employee_working_ids` 最新異動記錄決定狀態:
- `on_board/reinstatement/furlough` → `working`
- `resign` → `resign`
- 無記錄 → `draft`

### 保險級距自動更新

員工保險級距欄位為計算欄位，依據各保險異動歷程中最新生效的記錄自動更新。

### 破月計算

`is_partial_month()` 和 `get_partial_month_ratio()` 方法用於計算員工破月在職比例。

## 開發注意事項

1. **附件公開設定**: 所有 `ir.attachment` 相關欄位在 create/write 時會自動設為 `public = True`

2. **身分證驗證**: `hr.dependents.information` 模型包含台灣身分證格式驗證

3. **異動限制**: 在離職異動有邏輯檢查，必須先離職才能再到職

4. **政府補助設定**: 勞健保異動歷程包含政府補助比例設定

## 相關精靈

- 眷保新增精靈
- 勞保異動精靈
- 健保異動精靈
- 勞退異動精靈
- 職災保險異動精靈

## 視圖入口

主選單路徑: Starry Lord HRM

---

## 升級/安裝問題記錄

> **注意**: Odoo 19 通用升級問題請參考根目錄 `CLAUDE.md`

### 本模組修復記錄 (2026-01-12)

| 問題 | 檔案 | 修復內容 |
|------|------|----------|
| Many2one 缺少 comodel_name | `models/hr_employee.py:44` | 加入 `"res.country"` |
| 缺少資料檔 | `data/sl_employee_sequence.xml` | 新建檔案 |
| 缺少權限檔 | `security/ir.model.access.csv` | 新建檔案 |
| 缺少安全群組檔 | `security/sl_hrm_security.xml` | 新建檔案 |
| res.groups 欄位變更 | `security/sl_hrm_security.xml` | 移除 category_id, users |
| 缺少 wizard/views 檔案 | `wizard/`, `views/` | 從備份複製 |
| One2many 內嵌 tree 驗證錯誤 | `views/hr_employee.xml` | 建立獨立視圖 |
| tree 改為 list | `views/*.xml` | 批次替換 `<tree>` → `<list>` |
| gender 欄位不存在 | `models/hr_employee.py:61-70` | Odoo 19 移除了 gender 欄位，需自行定義 |
| skills_resume 頁面不存在 | `views/hr_employee.xml:382-395` | Odoo 19 改名為 resume，已註解 |
| group_by_skill_ids 過濾器不存在 | `views/hr_employee.xml:432-439` | Odoo 19 已移除，已註解 |
