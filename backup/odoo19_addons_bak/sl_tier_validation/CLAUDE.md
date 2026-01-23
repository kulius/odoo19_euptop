# SL Tier Validation Module (sl_tier_validation)

Starry Lord Base Tier Validation 擴充模組 - Odoo 19 多層簽核審批日誌擴充

## 模組概述

此模組擴充 OCA 的 `base_tier_validation` 模組，新增審批日誌 (Review Log) 功能，記錄每次簽核操作的歷史紀錄，並提供退回上一關功能。

**版本**: 19.0.1.0.0
**相依**: base, base_tier_validation
**授權**: LGPL-3

## 目錄結構

```
sl_tier_validation/
├── __init__.py
├── __manifest__.py
├── CLAUDE.md
├── models/                          # 主要模型
│   ├── __init__.py
│   ├── tier_validation.py           # 抽象模型擴充
│   ├── tier_review.py               # tier.review 擴充
│   └── tier_review_log.py           # 審批日誌模型
├── security/                        # 權限設定
│   ├── sl_tier_review_security.xml
│   └── ir.model.access.csv
├── static/                          # 前端資源
│   └── src/
│       └── components/
│           └── tier_review_log_widget/
│               ├── tier_review_log_widget.js
│               ├── tier_review_log_widget.scss
│               └── tier_review_log_widget.xml
├── templates/                       # QWeb 模板
│   └── tier_validation_templates.xml
├── views/                           # 視圖定義
│   ├── tier_portal_todo.xml
│   └── menu.xml
└── wizard/                          # 精靈對話框
    ├── __init__.py
    └── comment_wizard.py
```

## 核心模型

### 審批日誌 (tier.review.log)

**檔案**: `models/tier_review_log.py`

記錄每次簽核操作的歷史紀錄，包含核准、駁回等動作。

| 欄位 | 類型 | 說明 |
|------|------|------|
| `name` | Char | 定義名稱 (來自 tier.definition) |
| `status` | Selection | 狀態 (waiting/pending/rejected/approved) |
| `model` | Char | 關聯文件模型 |
| `res_id` | Integer | 關聯文件 ID |
| `definition_id` | Many2one | 簽核定義 |
| `company_id` | Many2one | 公司 |
| `review_type` | Selection | 審核類型 |
| `reviewer_id` | Many2one | 指定審核人 |
| `reviewer_group_id` | Many2one | 審核群組 |
| `reviewer_field_id` | Many2one | 審核人欄位 |
| `reviewer_ids` | Many2many | 審核人列表 |
| `sequence` | Integer | 層級 |
| `todo_by` | Char | 待審人 |
| `done_by` | Many2one | 審核人 |
| `requested_by` | Many2one | 發起人 |
| `reviewed_date` | Datetime | 審核日期 |
| `reviewed_formated_date` | Char | 格式化審核日期 (計算欄位) |
| `comment` | Char | 備註 |

狀態選項：
- `waiting`: 等待中
- `pending`: 待審核
- `rejected`: 已駁回
- `approved`: 已核准

---

### Tier Validation 抽象模型擴充 (tier.validation)

**檔案**: `models/tier_validation.py`

繼承 `base_tier_validation` 的抽象模型，新增日誌記錄功能。

#### 新增欄位

| 欄位 | 類型 | 說明 |
|------|------|------|
| `review_log_ids` | One2many | 審批日誌紀錄 |

#### 覆寫方法

| 方法 | 說明 |
|------|------|
| `_validate_tier()` | 核准時建立審批日誌 |
| `_rejected_tier()` | 駁回時建立審批日誌 |
| `get_view()` | 自動在表單視圖注入審批日誌元件 |

#### 新增方法

| 方法 | 說明 |
|------|------|
| `_rejected_to_previous_tier()` | 退回上一關功能 |
| `reject_to_previous_review_tier()` | 退回上一關入口 (含備註精靈) |
| `_get_previous_sequences_to_reject()` | 取得上一關的序號 |
| `_add_tier_validation_review_log()` | 注入審批日誌 QWeb 元件 |

---

### Tier Review 擴充 (tier.review)

**檔案**: `models/tier_review.py`

擴充原有的 `tier.review` 模型。

---

### 備註精靈擴充 (comment.wizard)

**檔案**: `wizard/comment_wizard.py`

擴充 `base_tier_validation` 的備註精靈，將 `comment` 欄位改為非必填。

---

## 前端元件

### Review Log Widget

**路徑**: `static/src/components/tier_review_log_widget/`

OWL 2 元件，用於在表單視圖中顯示審批日誌表格。

#### JavaScript (tier_review_log_widget.js)

```javascript
import { Component, useState } from "@odoo/owl";

export class ReviewLogTable extends Component {
    static template = "base_tier_validation.review_log.Collapse";
    // ...
}
```

#### 功能

- 可折疊的審批日誌面板
- 顯示每筆審核紀錄：說明、狀態、審核人、審核日期、備註
- 依狀態顯示不同樣式：
  - `waiting`: 灰色 (text-muted)
  - `pending`: 預設
  - `approved`: 綠色 (alert-success)
  - `rejected`: 紅色 (alert-danger)

---

## 視圖定義

### 待辦簽核 (tier.review)

**檔案**: `views/tier_portal_todo.xml`

| 視圖 | 說明 |
|------|------|
| `view_tier_portal_todo_tree` | 待辦簽核清單 |
| `view_tier_portal_todo_form` | 待辦簽核表單 |
| `view_tier_portal_todo_search` | 搜尋視圖 |

### 動作

| 動作 ID | 說明 | Domain |
|---------|------|--------|
| `action_tier_portal_todo` | 待辦簽核 | `[('reviewer_ids','in',uid), ('can_sign','=',True)]` |
| `action_tier_portal_todo_manager` | 待辦簽核管理 | 全部 |

---

## 權限群組

| 群組 ID | 名稱 | 說明 |
|---------|------|------|
| `group_sl_tier_review_manager` | 待辦簽核管理人員 | 管理待辦簽核 |

### 模組分類

- **名稱**: SL-待辦簽核
- **序號**: 22

---

## 自動注入機制

此模組會自動在所有繼承 `tier.validation` 的模型表單視圖中注入審批日誌面板：

1. 覆寫 `get_view()` 方法
2. 檢測 `view_type == "form"`
3. 在 `/form/sheet` 節點下注入 `tier_validation_review_log` 模板
4. 使用 `tier_review_log` widget 顯示日誌

---

## 工作流程

### 核准流程

1. 審核人點擊核准按鈕
2. 觸發 `_validate_tier()`
3. 建立狀態為 `approved` 的審批日誌
4. 呼叫父類方法完成核准

### 駁回流程

1. 審核人點擊駁回按鈕
2. 觸發 `_rejected_tier()`
3. 建立狀態為 `rejected` 的審批日誌
4. 呼叫父類方法完成駁回

### 退回上一關流程

1. 審核人點擊退回上一關按鈕
2. 觸發 `reject_to_previous_review_tier()`
3. 若需備註則顯示備註精靈
4. 觸發 `_rejected_to_previous_tier()`
5. 建立駁回日誌
6. 將上一關狀態設為 `pending`

---

## 開發注意事項

1. **OWL 2 語法**: JavaScript 元件使用 Odoo 19 的 OWL 2 語法
   - 使用 `import { Component, useState } from "@odoo/owl";`
   - 使用 `static template = ...`
   - 避免使用 jQuery，改用原生 JavaScript

2. **抽象模型繼承**: `tier.validation` 為抽象模型，使用 `_inherit` 繼承

3. **動態視圖注入**: `get_view()` 會動態修改視圖架構，需注意效能

4. **時區處理**: `reviewed_formated_date` 計算欄位會根據使用者時區轉換顯示

---

## 視圖入口

主選單路徑: 電子簽核 → 待辦簽核管理

(需具備 `group_sl_tier_review_manager` 群組權限)

---

## 與 base_tier_validation 的關係

此模組為 OCA `base_tier_validation` 的擴充：

| 功能 | base_tier_validation | sl_tier_validation |
|------|---------------------|-------------------|
| 多層簽核 | ✓ | ✓ (繼承) |
| 審批狀態 | ✓ | ✓ (繼承) |
| 審批日誌 | ✗ | ✓ (新增) |
| 退回上一關 | ✗ | ✓ (新增) |
| 日誌 Widget | ✗ | ✓ (新增) |

---

## 升級/安裝問題記錄

> **注意**: Odoo 19 通用升級問題請參考根目錄 `CLAUDE.md`

### 本模組修復記錄 (2026-01-12)

| 問題 | 檔案 | 修復內容 |
|------|------|----------|
| OWL 1 語法 | `static/src/.../tier_review_log_widget.js` | 更新為 OWL 2 語法 |
| jQuery 使用 | `static/src/.../tier_review_log_widget.js` | 改用原生 JavaScript |
| print 語句 | `models/tier_review.py` | 改用 logging |
| wizard 未 import | `__init__.py` | 加入 `from . import wizard` |
| model 未 import | `models/__init__.py` | 加入 `tier_portal_form` |
| 權限缺失 | `security/ir.model.access.csv` | 加入 `tier.portal.form` 權限 |
| view 未聲明 | `__manifest__.py` | 加入 `views/tier_portal_form.xml` |
