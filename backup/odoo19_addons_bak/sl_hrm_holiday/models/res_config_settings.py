from odoo import models, fields, api


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    holiday_special_id = fields.Many2one("starrylord.holiday.type", string="特休",
                                         config_parameter='sl_hrm_holiday.holiday_special_id')
    holiday_sick_id = fields.Many2one("starrylord.holiday.type", string="病假")
    holiday_leave_id = fields.Many2one("starrylord.holiday.type", string="事假")
    holiday_menstrual_id = fields.Many2one("starrylord.holiday.type", string="生理假")
    holiday_comp_id = fields.Many2one("starrylord.holiday.type", domain="[('request_unit', '!=', 'day')]", string="補休")
    cycle_calendar = fields.Selection([('cycle', '週年制'), ('calendar', '歷年制')], string="特休制度")

    def set_values(self):
        super(ResConfigSettings, self).set_values()
        params = self.env['ir.config_parameter']
        params.sudo().set_param('sl_hrm_holiday.holiday_special_id',
                                self.holiday_special_id.id)

        params.sudo().set_param('sl_hrm_holiday.holiday_sick_id', self.holiday_sick_id.id)
        params.sudo().set_param('sl_hrm_holiday.holiday_leave_id', self.holiday_leave_id.id)
        params.sudo().set_param('sl_hrm_holiday.holiday_menstrual_id', self.holiday_menstrual_id.id)
        params.sudo().set_param('sl_hrm_holiday.holiday_comp_id', self.holiday_comp_id.id)
        params.sudo().set_param('sl_hrm_holiday.cycle_calendar', self.cycle_calendar)

    @api.model
    def get_values(self):
        res = super(ResConfigSettings, self).get_values()
        params = self.env['ir.config_parameter']
        holiday_special_id = params.sudo().get_param('sl_hrm_holiday.holiday_special_id', default=False)
        holiday_sick_id = params.sudo().get_param('sl_hrm_holiday.holiday_sick_id', default=False)
        holiday_leave_id = params.sudo().get_param('sl_hrm_holiday.holiday_leave_id', default=False)
        holiday_menstrual_id = params.sudo().get_param('sl_hrm_holiday.holiday_menstrual_id', default=False)
        holiday_comp_id = params.sudo().get_param('sl_hrm_holiday.holiday_comp_id', default=False)
        cycle_calendar = params.sudo().get_param('sl_hrm_holiday.cycle_calendar', 'cycle')

        res.update({
            'holiday_special_id': int(holiday_special_id) if holiday_special_id else False,
            'holiday_sick_id': int(holiday_sick_id) if holiday_sick_id else False,
            'holiday_leave_id': int(holiday_leave_id) if holiday_leave_id else False,
            'holiday_menstrual_id': int(holiday_menstrual_id) if holiday_menstrual_id else False,
            'holiday_comp_id': int(holiday_comp_id) if holiday_comp_id else False,
            'cycle_calendar': cycle_calendar
        })
        return res

    def holiday_hour_list_action_go(self):
        return self.env.ref('sl_hrm_holiday.starrylord_holiday_hour_list_action').read()[0]

    def holiday_min_list_action_go(self):
        return self.env.ref('sl_hrm_holiday.starrylord_holiday_min_list_action').read()[0]
