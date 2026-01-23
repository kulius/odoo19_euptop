import math
import datetime
from odoo import api, fields, models
from odoo.exceptions import UserError
from dateutil.relativedelta import relativedelta


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    # ========== 從 sl_hrm_holiday 合併 ==========
    holiday_special_id = fields.Many2one("starrylord.holiday.type", string="特休",
                                         config_parameter='sl_hrm_holiday.holiday_special_id')
    holiday_sick_id = fields.Many2one("starrylord.holiday.type", string="病假")
    holiday_leave_id = fields.Many2one("starrylord.holiday.type", string="事假")
    holiday_menstrual_id = fields.Many2one("starrylord.holiday.type", string="生理假")
    holiday_comp_id = fields.Many2one("starrylord.holiday.type", domain="[('request_unit', '!=', 'day')]", string="補休")
    cycle_calendar = fields.Selection([('cycle', '週年制'), ('calendar', '歷年制')], string="特休制度")

    # ========== 從 sl_hrm_overtime 合併 ==========
    max_overtime_month = fields.Integer(string="單月加班時數上限")
    max_overtime_three_month = fields.Integer(string="三月內加班時數上限")
    is_hr_check_overtime = fields.Boolean(string="是否要人資進行確認")
    start_overtime = fields.Integer(string="加班起算時間(分)")
    min_overtime_unit = fields.Selection(
        [
            ('hour', '1 小時'),
            ('half', '30 分鐘'),
            ('quarter', '15 分鐘'),
        ],
        string="最小加班單位",
        default='half',
        required=True,
    )

    def set_values(self):
        super(ResConfigSettings, self).set_values()
        params = self.env['ir.config_parameter']

        # Holiday settings
        params.sudo().set_param('sl_hrm_holiday.holiday_special_id',
                                self.holiday_special_id.id)
        params.sudo().set_param('sl_hrm_holiday.holiday_sick_id', self.holiday_sick_id.id)
        params.sudo().set_param('sl_hrm_holiday.holiday_leave_id', self.holiday_leave_id.id)
        params.sudo().set_param('sl_hrm_holiday.holiday_menstrual_id', self.holiday_menstrual_id.id)
        params.sudo().set_param('sl_hrm_holiday.holiday_comp_id', self.holiday_comp_id.id)
        params.sudo().set_param('sl_hrm_holiday.cycle_calendar', self.cycle_calendar)

        # Overtime settings
        params.sudo().set_param('max_overtime_month', self.max_overtime_month)
        params.sudo().set_param('max_overtime_three_month', self.max_overtime_three_month)
        params.sudo().set_param('is_hr_check_overtime', self.is_hr_check_overtime)
        params.sudo().set_param('start_overtime', self.start_overtime)
        params.sudo().set_param('min_overtime_unit', self.min_overtime_unit)

    def overtime_daily_code(self):
        self.env['ir.sequence'].sudo().search([('code', '=', 'starrylord_overtime_number')],
                                              order="create_date desc", limit=1).number_next_actual = 1

    @api.model
    def get_values(self):
        res = super(ResConfigSettings, self).get_values()
        params = self.env['ir.config_parameter'].sudo()

        # Holiday settings
        holiday_special_id = params.get_param('sl_hrm_holiday.holiday_special_id', default=False)
        holiday_sick_id = params.get_param('sl_hrm_holiday.holiday_sick_id', default=False)
        holiday_leave_id = params.get_param('sl_hrm_holiday.holiday_leave_id', default=False)
        holiday_menstrual_id = params.get_param('sl_hrm_holiday.holiday_menstrual_id', default=False)
        holiday_comp_id = params.get_param('sl_hrm_holiday.holiday_comp_id', default=False)
        cycle_calendar = params.get_param('sl_hrm_holiday.cycle_calendar', 'cycle')

        # Overtime settings
        max_overtime_month = params.get_param('max_overtime_month', default=False)
        max_overtime_three_month = params.get_param('max_overtime_three_month', default=False)
        is_hr_check_overtime = params.get_param('is_hr_check_overtime', default=False)
        start_overtime = params.get_param('start_overtime', default=False)
        min_overtime_unit = params.get_param('min_overtime_unit', default=False)

        res.update({
            # Holiday settings
            'holiday_special_id': int(holiday_special_id) if holiday_special_id else False,
            'holiday_sick_id': int(holiday_sick_id) if holiday_sick_id else False,
            'holiday_leave_id': int(holiday_leave_id) if holiday_leave_id else False,
            'holiday_menstrual_id': int(holiday_menstrual_id) if holiday_menstrual_id else False,
            'holiday_comp_id': int(holiday_comp_id) if holiday_comp_id else False,
            'cycle_calendar': cycle_calendar,
            # Overtime settings
            'max_overtime_month': int(max_overtime_month) if max_overtime_month else False,
            'max_overtime_three_month': int(max_overtime_three_month) if max_overtime_three_month else False,
            'is_hr_check_overtime': is_hr_check_overtime if is_hr_check_overtime else False,
            'start_overtime': start_overtime if start_overtime else False,
            'min_overtime_unit': min_overtime_unit if min_overtime_unit else False,
        })
        return res

    def holiday_hour_list_action_go(self):
        return self.env.ref('sl_hrm.starrylord_holiday_hour_list_action').read()[0]

    def holiday_min_list_action_go(self):
        return self.env.ref('sl_hrm.starrylord_holiday_min_list_action').read()[0]
