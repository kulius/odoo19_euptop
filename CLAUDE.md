# Odoo 19 EupTop 專案

## 專案結構

```
odoo19_euptop/
├── addons_store/      # 自訂模組
├── odoo-19.0/         # Odoo 核心
└── CLAUDE.md          # 本文件
```

## 開發環境

- **Odoo 版本**: 19.0
- **Python**: 3.12+
- **資料庫**: PostgreSQL

---

# Odoo 19 升級注意事項

從舊版本升級至 Odoo 19 時，需注意以下重大變更。

## 1. Many2one 欄位必須指定 comodel_name

**錯誤訊息**:
```
AssertionError: Field xxx.xxx with unknown comodel_name '???'
```

**原因**: Odoo 19 中覆寫 Many2one 欄位時，必須明確指定 `comodel_name`

**修復**:
```python
# 錯誤寫法
country_id = fields.Many2one(
    default=lambda self: self.env.company.country_id)

# 正確寫法
country_id = fields.Many2one(
    "res.country", default=lambda self: self.env.company.country_id)
```

---

## 2. res.groups 移除 category_id 和 users 欄位

**錯誤訊息**:
```
ValueError: Invalid field 'category_id' in 'res.groups'
ValueError: Invalid field 'users' in 'res.groups'
```

**原因**: Odoo 19 的 `res.groups` 模型結構變更，移除了以下欄位：
- `category_id` - 分類欄位
- `users` - 使用者欄位

**修復**: 從安全群組 XML 定義中移除這些欄位

```xml
<!-- 錯誤寫法 (Odoo 18 及之前) -->
<record id="group_xxx" model="res.groups">
    <field name="name">Group Name</field>
    <field name="category_id" ref="base.module_category_xxx"/>
    <field name="users" eval="[(4, ref('base.user_admin'))]"/>
</record>

<!-- 正確寫法 (Odoo 19) -->
<record id="group_xxx" model="res.groups">
    <field name="name">Group Name</field>
    <field name="implied_ids" eval="[(4, ref('base.group_user'))]"/>
</record>
```

---

## 3. manifest 中宣告的檔案必須存在

**錯誤訊息**:
```
FileNotFoundError: [Errno 2] No such file or directory: 'xxx/xxx.xml'
```

**原因**: `__manifest__.py` 中 `data` 列表宣告的檔案實際不存在

**檢查清單**:
- `data/` 資料夾中的 XML 檔案
- `security/ir.model.access.csv`
- `security/xxx_security.xml`
- `views/` 資料夾中的 XML 檔案
- `wizard/` 資料夾中的 XML 檔案

---

## 4. 安全檔案範本

### ir.model.access.csv 範本

```csv
id,name,model_id:id,group_id:id,perm_read,perm_write,perm_create,perm_unlink
access_model_name_user,model.name.user,model_model_name,hr.group_hr_user,1,1,1,1
```

**注意**:
- `model_id:id` 格式為 `model_` + 模型名稱(將 `.` 替換為 `_`)
- 例如: `hr.employee` → `model_hr_employee`

### security.xml 範本

```xml
<?xml version="1.0" encoding="utf-8"?>
<odoo>
    <data noupdate="0">
        <record id="group_xxx_user" model="res.groups">
            <field name="name">XXX User</field>
            <field name="implied_ids" eval="[(4, ref('base.group_user'))]"/>
        </record>

        <record id="group_xxx_manager" model="res.groups">
            <field name="name">XXX Manager</field>
            <field name="implied_ids" eval="[(4, ref('group_xxx_user'))]"/>
        </record>
    </data>
</odoo>
```

---

## 5. 常見模型繼承問題

### 繼承欄位需完整定義

當繼承父模型並修改欄位屬性時，某些參數需要重新指定：

```python
# 繼承並修改 Many2one 欄位
class MyModel(models.Model):
    _inherit = "parent.model"

    # 需要指定 comodel_name
    field_id = fields.Many2one("res.partner", default=lambda self: ...)
```

---

## 更新記錄

| 日期 | 模組 | 問題描述 |
|------|------|----------|
| 2026-01-12 | sl_hrm | country_id 缺少 comodel_name |
| 2026-01-12 | sl_hrm | 缺少 data/sl_employee_sequence.xml |
| 2026-01-12 | sl_hrm | 缺少 security 檔案 |
| 2026-01-12 | sl_hrm | res.groups 移除 category_id, users |
| 2026-01-12 | sl_hrm | 缺少 wizard/views 檔案 (從 backup 複製) |
| 2026-01-12 | sl_hrm | One2many 內嵌 tree 驗證錯誤 |
| 2026-01-12 | sl_hrm | tree 改為 list |
| 2026-01-12 | sl_hrm | gender 欄位不存在 (Odoo 19 移除) |
| 2026-01-12 | sl_hrm | skills_resume 頁面改名為 resume |
| 2026-01-12 | sl_hrm | group_by_skill_ids 過濾器已移除 |
| 2026-01-12 | sl_hrm | xpath expr="//tree" 找不到 (父視圖已改為 list) |
| 2026-01-12 | sl_hrm | view_mode 中的 tree 需改為 list |
| 2026-01-12 | sl_hrm | Many2many 欄位使用錯誤參數 inverse_name |
| 2026-01-12 | sl_hrm | required 欄位含 null 值導致安裝失敗 |
| 2026-01-12 | sl_hrm | 缺少 sl.company.site 模型安全權限 |
| 2026-01-13 | sl_hr_attendance | groups_id 改為 group_ids |
| 2026-01-13 | sl_hr_attendance | 移除不存在的 kiosk 選單引用 |
| 2026-01-13 | sl_hr_attendance | 移除有問題的 search view |
| 2026-01-13 | sl_hr_attendance | wizard 缺少 _description |
| 2026-01-13 | sl_hr_attendance | OWL 元件需升級 (暫時停用 assets) |

---

## 6. 備份資料夾 (Odoo 17 版本)

當模組升級時發現缺少 XML/Python 檔案，先檢查 `backup/` 資料夾是否有備份。

**注意**: backup 資料夾是 Odoo 17 版本，複製後需要升級！

```bash
# 複製備份檔案
cp -r backup/模組名稱/wizard/* addons_store/模組名稱/wizard/
cp -r backup/模組名稱/views/* addons_store/模組名稱/views/
```

---

## 7. Odoo 17 → 19 升級檢查清單

### Python 檔案

1. **所有模型必須有 `_description`**
```python
# 錯誤
class MyModel(models.Model):
    _name = 'my.model'

# 正確
class MyModel(models.Model):
    _name = 'my.model'
    _description = '我的模型'
```

2. **覆寫 Many2one 欄位需指定 comodel_name**
```python
# 錯誤
country_id = fields.Many2one(default=lambda self: ...)

# 正確
country_id = fields.Many2one("res.country", default=lambda self: ...)
```

### XML 檔案

1. **`tree` 改為 `list`** (視圖定義)
```xml
<!-- Odoo 17 (舊) -->
<tree editable="bottom">...</tree>

<!-- Odoo 19 (新) -->
<list editable="bottom">...</list>
```

2. **`view_mode` 中的 `tree` 改為 `list`** (action 定義)
```xml
<!-- Odoo 17 (舊) -->
<field name="view_mode">tree,form</field>
<field name="view_mode">tree,kanban,form</field>

<!-- Odoo 19 (新) -->
<field name="view_mode">list,form</field>
<field name="view_mode">list,kanban,form</field>
```

3. **xpath 中的 `//tree` 改為 `//list`** (繼承視圖)
```xml
<!-- Odoo 17 (舊) -->
<xpath expr="//tree" position="replace">

<!-- Odoo 19 (新) -->
<xpath expr="//list" position="replace">
```
**注意**: 如果父視圖已升級為 `<list>`，xpath 必須相應更新

4. **`attrs` 屬性已移除** - 改用直接屬性
```xml
<!-- Odoo 17 (舊) -->
<field name="x" attrs="{'invisible': [('state', '=', 'draft')]}"/>

<!-- Odoo 19 (新) -->
<field name="x" invisible="state == 'draft'"/>
```

5. **`states` 屬性已移除** - 改用 `invisible`
```xml
<!-- Odoo 17 (舊) -->
<button states="draft"/>

<!-- Odoo 19 (新) -->
<button invisible="state != 'draft'"/>
```

6. **res.groups 變更**
- 移除 `category_id` 欄位
- 移除 `users` 欄位

### Security 檔案

確保 `ir.model.access.csv` 包含所有模型，包括 wizard (TransientModel)

### One2many 內嵌視圖

Odoo 19 對 One2many 欄位內嵌的 tree 視圖驗證更嚴格。建議改為獨立定義視圖：

```xml
<!-- 舊寫法 (可能導致驗證錯誤) -->
<field name="line_ids">
    <tree editable="bottom">
        <field name="name"/>
    </tree>
</field>

<!-- 新寫法: 先定義獨立視圖 -->
<record id="view_my_line_tree" model="ir.ui.view">
    <field name="name">my.line.tree</field>
    <field name="model">my.line.model</field>
    <field name="arch" type="xml">
        <tree editable="bottom">
            <field name="name"/>
        </tree>
    </field>
</record>

<!-- 然後在表單中只引用欄位 -->
<field name="line_ids" nolabel="1"/>

---

## 8. hr.employee 移除的欄位

Odoo 19 的 `hr.employee` 模型移除了部分欄位，若模組使用這些欄位需自行定義：

| 欄位 | 類型 | 說明 |
|------|------|------|
| `gender` | Selection | 性別 (male/female/other) |

---

## 9. hr_skills 模組頁面名稱變更

Odoo 19 中 `hr_skills` 模組的頁面名稱有變更：

| Odoo 17 | Odoo 19 |
|---------|---------|
| `skills_resume` | `resume` |

**修復**: 更新 xpath 中的頁面名稱，或註解掉相關視圖

```xml
<!-- Odoo 17 (舊) -->
<xpath expr="//page[@name='skills_resume']" position="...">

<!-- Odoo 19 (新) -->
<xpath expr="//page[@name='resume']" position="...">
```

---

**修復範例** (在繼承的模型中新增):
```python
# 性別 (Odoo 19 移除了此欄位，需自行定義)
gender = fields.Selection(
    selection=[
        ("male", "男"),
        ("female", "女"),
        ("other", "其他"),
    ],
    string="性別",
    groups="hr.group_hr_user",
)
```

---

## 10. Many2many 欄位參數錯誤

**錯誤訊息**:
```
WARNING: Field xxx.xxx: unknown parameter 'inverse_name'
```

**原因**: `inverse_name` 是 One2many 的參數，Many2many 應使用 `relation`

**修復**:
```python
# 錯誤寫法
book_cover = fields.Many2many(
    "ir.attachment", string="附件", inverse_name="xxx_ids"
)

# 正確寫法
book_cover = fields.Many2many(
    "ir.attachment", string="附件", relation="xxx_attachment_rel"
)
```

---

## 11. required 欄位與既有資料衝突

**錯誤訊息**:
```
ERROR: column "xxx" of relation "xxx" contains null values
Missing not-null constraint on xxx.xxx
```

**原因**: 新增 `required=True` 欄位，但資料庫中既有記錄為 null

**修復方案**:

1. **移除 required，改用 default**:
```python
# 錯誤寫法
prefix = fields.Char(string="前綴", required=True)

# 正確寫法
prefix = fields.Char(string="前綴", default="")
```

2. **或先更新既有資料後再加 required**

---

## 12. 模組升級驗證指令

### 使用 --update (已安裝模組)

```bash
python odoo-bin --config=xxx.conf --database=xxx --update=模組名稱 --stop-after-init
```

**注意**: `--update` 只會更新已安裝的模組，不會完整驗證 XML

### 使用 --init (完整安裝測試)

```bash
python odoo-bin --config=xxx.conf --database=xxx --init=模組名稱 --stop-after-init
```

**建議**: 升級模組後使用 `--init` 進行完整測試，可發現更多問題

---

## 13. 常見升級問題快速檢查

使用以下指令快速檢查常見問題：

```bash
# 檢查 view_mode 中的 tree
grep -r "view_mode.*tree" views/*.xml

# 檢查 xpath 中的 //tree
grep -r 'xpath.*//tree' views/*.xml

# 檢查 attrs 屬性
grep -r 'attrs\s*=' views/*.xml

# 檢查 <tree> 標籤
grep -r '<tree' views/*.xml

# 檢查 groups_id (已改為 groups)
grep -r 'groups_id' views/*.xml
```

---

## 14. ir.ui.menu 欄位名稱

**錯誤訊息**:
```
ValueError: Invalid field 'groups_id' in 'ir.ui.menu'
ValueError: Invalid field 'groups' in 'ir.ui.menu'
```

**原因**: `ir.ui.menu` 模型的群組欄位正確名稱是 `group_ids`

**修復**:
```xml
<!-- 錯誤寫法 -->
<record id="menu_xxx" model="ir.ui.menu">
    <field name="groups_id" eval="[(4, ref('base.group_user'))]"/>
</record>

<!-- 正確寫法 -->
<record id="menu_xxx" model="ir.ui.menu">
    <field name="group_ids" eval="[(4, ref('base.group_user'))]"/>
</record>
```

---

## 15. 繼承的選單 ID 可能不存在

**錯誤訊息**:
```
Exception: Cannot update missing record 'module.menu_xxx'
```

**原因**: Odoo 19 中選單結構已改變，某些選單 ID 已不存在

**檢查方式**: 在 Odoo 核心模組的 views 資料夾中搜尋 menuitem 定義

**修復**: 移除引用不存在選單 ID 的 record

---

## 16. OWL 前端元件相容性

**錯誤訊息** (瀏覽器 Console):
```
Error: Service rpc is not available
owl.js:xxx OwlError
```

**原因**: 自訂 OWL 元件使用了 Odoo 19 中已變更或移除的服務/API

**常見問題**:
- `useService("rpc")` 必須確保 rpc 服務已正確註冊
- 自訂 controller endpoint 可能尚未建立
- 元件的生命週期方法可能有變更

**暫時修復**: 在 `__manifest__.py` 中註解掉 assets 區塊

```python
# 'assets': {
#     'web.assets_backend': [
#         'my_module/static/src/**/*',
#     ],
# },  # TODO: Fix OWL components for Odoo 19
```

---

## 17. Search View 驗證錯誤

**錯誤訊息**:
```
View xxx.xxx.search 定義無效
```

**原因**: Odoo 19 對搜尋視圖的驗證更嚴格

**常見問題**:
- `filter_domain` 語法變更
- `default_period` 等屬性可能已移除
- datetime 欄位的 `date` groupby 可能不支援

**暫時修復**: 移除有問題的搜尋視圖，使用系統預設搜尋

---

## 18. hr_attendance 模組選單 ID 變更

Odoo 19 中 `hr_attendance` 模組的選單結構有變更：

| 已移除的選單 ID |
|----------------|
| `hr_attendance.menu_hr_attendance_kiosk_no_user_mode` |
| `hr_attendance.menu_hr_attendance_kiosk_no_pin_mode` |

**修復**: 移除對這些選單的引用
