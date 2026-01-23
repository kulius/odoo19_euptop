import math
import datetime
from odoo import api, fields, models
from odoo.exceptions import UserError
from dateutil.relativedelta import relativedelta


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

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
        res = super(ResConfigSettings, self).set_values()
        params = self.env['ir.config_parameter']
        params.sudo().set_param('max_overtime_month', self.max_overtime_month)
        params.sudo().set_param('max_overtime_three_month', self.max_overtime_three_month)
        params.sudo().set_param('is_hr_check_overtime', self.is_hr_check_overtime)
        params.sudo().set_param('start_overtime', self.start_overtime)
        params.sudo().set_param('min_overtime_unit', self.min_overtime_unit)
        # params.sudo().set_param('sl_hrm_overtime.sl_holiday_type_id', self.sl_holiday_type_id.id)

    def overtime_daily_code(self):
        self.env['ir.sequence'].sudo().search([('code', '=', 'starrylord_overtime_number')],
                                              order="create_date desc", limit=1).number_next_actual = 1

    @api.model
    def get_values(self):
        res = super(ResConfigSettings, self).get_values()
        params = self.env['ir.config_parameter'].sudo()
        max_overtime_month = params.get_param('max_overtime_month', default=False)
        max_overtime_three_month = params.get_param('max_overtime_three_month', default=False)
        is_hr_check_overtime = params.get_param('is_hr_check_overtime', default=False)
        start_overtime = params.get_param('start_overtime', default=False)
        min_overtime_unit = params.get_param('min_overtime_unit', default=False)
        # sl_holiday_type_id = params.sudo().get_param('sl_hrm_overtime.sl_holiday_type_id', default=False)
        res.update({
            'max_overtime_month': int(max_overtime_month) if max_overtime_month else False,
            'max_overtime_three_month': int(max_overtime_three_month) if max_overtime_three_month else False,
            'is_hr_check_overtime': is_hr_check_overtime if is_hr_check_overtime else False,
            'start_overtime': start_overtime if start_overtime else False,
            'min_overtime_unit': min_overtime_unit if min_overtime_unit else False,
            # 'sl_hrm_overtime.sl_holiday_type_id': int(sl_holiday_type_id) if sl_holiday_type_id else False,
        })
        return res
