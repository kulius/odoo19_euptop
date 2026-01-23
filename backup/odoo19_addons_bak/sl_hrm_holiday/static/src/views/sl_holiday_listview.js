/** @odoo-module **/

import { registry } from "@web/core/registry";
import { listView } from "@web/views/list/list_view";
import { ListRenderer } from "@web/views/list/list_renderer";
import { StarryLordHolidayDashBoard } from '@sl_hrm_holiday/views/sl_holiday_dashboard';

export class StarryLordHolidayDashBoardRenderer extends ListRenderer {};

StarryLordHolidayDashBoardRenderer.template = 'sl_hrm_holiday.HolidayListView';
StarryLordHolidayDashBoardRenderer.components= Object.assign({}, ListRenderer.components, {StarryLordHolidayDashBoard})

export const StarryLordHolidayDashBoardListView = {
    ...listView,
    Renderer: StarryLordHolidayDashBoardRenderer,
};

registry.category("views").add("sl_hrm_holiday_dashboard_list", StarryLordHolidayDashBoardListView);
