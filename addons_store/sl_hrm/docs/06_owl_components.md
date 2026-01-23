# OWL 前端元件 (OWL Components)

本文件說明 sl_hrm 模組的 OWL 前端元件。

---

## 概述

sl_hrm 模組包含自訂 OWL 元件，用於增強使用者介面體驗。

**位置**: `static/src/views/`

---

## 請休假儀表板 (Holiday Dashboard)

### 元件架構

```
static/src/views/
├── sl_holiday_dashboard.js      # Dashboard 元件
├── sl_holiday_dashboard.xml     # Dashboard 範本
├── sl_holiday_listview.js       # 自訂 ListView
└── sl_holiday_listview.xml      # ListView 範本
```

### 註冊名稱

```javascript
registry.category("views").add("sl_hrm_holiday_dashboard_list", StarryLordHolidayDashBoardListView);
```

### 使用方式

在 list view 加入 `js_class` 屬性:

```xml
<list js_class="sl_hrm_holiday_dashboard_list">
    ...
</list>
```

---

### sl_holiday_dashboard.js

**類別**: `StarryLordHolidayDashBoard`
**範本**: `sl_hrm.HolidayDashboard`

```javascript
export class StarryLordHolidayDashBoard extends Component {
    static template = "sl_hrm.HolidayDashboard";

    setup() {
        this.orm = useService("orm");
        this.action = useService("action");

        onWillStart(async () => {
            this.holidayData = await this.orm.call(
                "starrylord.holiday.apply",
                "retrieve_dashboard"
            );
        });
    }
}
```

### API 呼叫

**Model**: `starrylord.holiday.apply`
**Method**: `retrieve_dashboard`

**回傳資料**:

```javascript
{
    annual_leave_hours: 80,        // 特休剩餘小時
    sick_leave_hours: 30,          // 病假剩餘小時
    compensation_leave_hours: 16,  // 補休剩餘小時
    private_leave_hours: 14,       // 事假剩餘小時
    menstrual_leave_hours: 8,      // 生理假剩餘小時
    gender: "female"               // 員工性別
}
```

---

### sl_holiday_dashboard.xml

**範本名稱**: `sl_hrm.HolidayDashboard`

顯示以下假別剩餘時數:

| 顯示 | 資料欄位 | 條件 |
|------|----------|------|
| 特休剩餘 | `annual_leave_hours` | 永遠顯示 |
| 病假剩餘 | `sick_leave_hours` | 永遠顯示 |
| 生理假剩餘 | `menstrual_leave_hours` | 僅女性顯示 |
| 補休剩餘 | `compensation_leave_hours` | 永遠顯示 |
| 事假剩餘 | `private_leave_hours` | 永遠顯示 |

---

### sl_holiday_listview.js

**類別**: `StarryLordHolidayDashBoardRenderer`
**繼承**: `ListRenderer`

```javascript
export class StarryLordHolidayDashBoardRenderer extends ListRenderer {
    static template = "sl_hrm.HolidayListView";
    static components = {
        ...ListRenderer.components,
        StarryLordHolidayDashBoard
    };
}
```

---

### sl_holiday_listview.xml

**範本名稱**: `sl_hrm.HolidayListView`
**繼承**: `web.ListRenderer`

在列表視圖上方插入 Dashboard:

```xml
<t t-name="sl_hrm.HolidayListView"
   t-inherit="web.ListRenderer"
   t-inherit-mode="primary">
    <xpath expr="//div[hasclass('o_list_renderer')]" position="before">
        <StarryLordHolidayDashBoard />
    </xpath>
</t>
```

---

## Manifest 設定

在 `__manifest__.py` 中註冊 assets:

```python
'assets': {
    'web.assets_backend': [
        'sl_hrm/static/src/views/*.js',
        'sl_hrm/static/src/views/*.xml',
    ],
},
```

---

## Odoo 19 OWL 升級注意事項

### 1. 模組宣告

```javascript
/** @odoo-module */
// 或
/** @odoo-module **/
```

### 2. 匯入方式

```javascript
// OWL 核心
import { Component, onWillStart } from "@odoo/owl";

// Odoo 服務
import { useService } from "@web/core/utils/hooks";

// 視圖相關
import { registry } from "@web/core/registry";
import { listView } from "@web/views/list/list_view";
import { ListRenderer } from "@web/views/list/list_renderer";
```

### 3. 元件定義

```javascript
export class MyComponent extends Component {
    static template = "module.TemplateName";
    static components = { ...ParentComponent.components, ChildComponent };

    setup() {
        // 初始化邏輯
    }
}
```

### 4. 視圖註冊

```javascript
export const MyCustomListView = {
    ...listView,
    Renderer: MyCustomRenderer,
};

registry.category("views").add("my_custom_list", MyCustomListView);
```

---

## 除錯

### 常見錯誤

**錯誤**: `Cannot find key "xxx" in the "views" registry`

**原因**:
1. JS 檔案未正確載入
2. Manifest assets 設定錯誤
3. 模組未更新

**解決**:
1. 檢查 `__manifest__.py` 的 assets 設定
2. 更新模組: `--update=sl_hrm`
3. 清除瀏覽器快取
4. 檢查瀏覽器 Console 是否有 JS 錯誤

---

**錯誤**: `OwlError` 或 `Service xxx is not available`

**原因**:
1. 使用了不存在的服務
2. OWL 生命週期問題

**解決**:
1. 確認服務名稱正確 (如 `orm`, `action`, `notification`)
2. 檢查 `setup()` 方法中的初始化邏輯
