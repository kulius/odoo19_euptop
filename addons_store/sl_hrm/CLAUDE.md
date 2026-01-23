# SL HRM Module (sl_hrm)

Starry Lord HRM 人資管理整合模組 - Odoo 19

## 模組概述

此模組為台灣人力資源管理系統，整合以下功能：

- 人資基本資料管理（勞健保、勞退）
- 個人行事曆與排班
- 請假申請與管理
- 加班申請與管理
- 考勤打卡與管理

**版本**: 19.0.2.0.0
**相依**: base, hr, hr_skills, hr_attendance, base_tier_validation, sl_tier_validation
**授權**: LGPL-3

---

## 文件索引

| 文件 | 說明 |
|------|------|
| [docs/01_core_hr.md](docs/01_core_hr.md) | 核心人資功能（員工、保險、體檢證照） |
| [docs/02_holiday.md](docs/02_holiday.md) | 請休假管理 |
| [docs/03_overtime.md](docs/03_overtime.md) | 加班管理 |
| [docs/04_attendance.md](docs/04_attendance.md) | 考勤管理 |
| [docs/05_personal_calendar.md](docs/05_personal_calendar.md) | 個人行事曆與排班 |
| [docs/06_owl_components.md](docs/06_owl_components.md) | OWL 前端元件 |

---

## 目錄結構

```
sl_hrm/
├── __init__.py
├── __manifest__.py
├── CLAUDE.md                    # 本文件 (索引)
├── docs/                        # 詳細文件
│   ├── 01_core_hr.md
│   ├── 02_holiday.md
│   ├── 03_overtime.md
│   ├── 04_attendance.md
│   ├── 05_personal_calendar.md
│   └── 06_owl_components.md
├── data/                        # 資料檔
├── job/                         # 自動化排程
├── models/                      # 模型
├── report/                      # 報表
├── security/                    # 權限
├── static/src/views/            # OWL 元件
├── views/                       # 視圖
└── wizard/                      # 精靈
```

---

## 模組合併歷程

此模組整合了以下原獨立模組，以解決循環相依問題：

| 原模組 | 功能 | 合併日期 |
|--------|------|----------|
| sl_hrm | 核心人資 | (原始) |
| sl_hrm_holiday | 請休假 | 2026-01-23 |
| sl_hrm_overtime | 加班 | 2026-01-23 |
| sl_hrm_personal_calendar | 個人行事曆 | 2026-01-23 |
| sl_hr_attendance | 考勤 | 2026-01-23 |

---

## 安全群組

### 核心人資群組

| 群組 ID | 說明 |
|---------|------|
| `group_sl_hrm_user` | HRM 使用者 |
| `group_sl_hrm_manager` | HRM 管理員 |

### 請休假群組

| 群組 ID | 說明 |
|---------|------|
| `group_starrylord_holiday_developer` | 請休假開發者 |
| `group_starrylord_holiday_manager` | 請休假管理員 |
| `group_starrylord_holiday_director` | 請休假主管 |

### 加班群組

| 群組 ID | 說明 |
|---------|------|
| `group_starrylord_overtime_developer` | 加班開發者 |
| `group_starrylord_overtime_manager` | 加班管理員 |
| `group_starrylord_overtime_director` | 加班主管 |

---

## 外部依賴

```python
'external_dependencies': {
    'python': ['pandas', 'openpyxl'],
},
```

---

## 主選單結構

```
Starry Lord HRM
├── 員工
├── 請休假
│   ├── 我的假單
│   ├── 請假單審核
│   ├── 休假管理
│   ├── 假別設定
│   └── 設定
├── 加班
│   ├── 我的加班單
│   ├── 加班單審核
│   ├── 加班管理
│   ├── 補休換取
│   └── 設定
├── 考勤
│   ├── 打卡記錄
│   ├── 考勤核對
│   ├── 補打卡申請
│   └── 匯入
├── 個人行事曆
└── 設定
```

---

## 升級/安裝問題記錄

> **通用 Odoo 19 升級問題**: 請參考根目錄 `CLAUDE.md`

### 本模組修復記錄

| 日期 | 問題 | 修復 |
|------|------|------|
| 2026-01-12 | Many2one 缺少 comodel_name | 加入 comodel_name |
| 2026-01-12 | 缺少 security 檔案 | 新建檔案 |
| 2026-01-12 | res.groups 欄位變更 | 移除 category_id, users |
| 2026-01-12 | tree 改為 list | 批次替換 |
| 2026-01-12 | gender 欄位不存在 | 自行定義 |
| 2026-01-13 | groups_id 改為 group_ids | 更新 base_tier_validation |
| 2026-01-23 | 模組合併解決循環相依 | 整合 5 個模組 |
| 2026-01-23 | OWL Dashboard 升級 | 升級至 Odoo 19 OWL |

---

## 開發注意事項

1. **附件公開設定**: `ir.attachment` 欄位自動設為 `public = True`

2. **身分證驗證**: `hr.dependents.information` 包含台灣身分證驗證

3. **異動限制**: 在離職異動有邏輯檢查

4. **OWL 元件**: 前端元件位於 `static/src/views/`，使用 Odoo 19 OWL 3 語法

5. **系統參數**: 請休假/加班功能依賴 `ir.config_parameter` 設定

---

## 快速開發指南

### 更新模組

```bash
python odoo-bin --config=xxx.conf --database=xxx --update=sl_hrm --stop-after-init
```

### 測試 OWL 元件

1. 更新模組
2. 清除瀏覽器快取 (Ctrl+Shift+Delete)
3. 重新整理頁面 (Ctrl+F5)
4. 檢查瀏覽器 Console 是否有錯誤
