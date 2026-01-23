from odoo import models, fields, api


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    regular_holiday_exclude_payroll = fields.Boolean(string='薪資計算排除例假日',)
    tax_baseline_amount = fields.Integer(string="扣繳5%薪資金額",
                                         config_parameter='sl_hrm_payroll.tax_baseline_amount')

    def set_values(self):
        super(ResConfigSettings, self).set_values()
        params = self.env['ir.config_parameter']
        params.sudo().set_param('sl_hrm_payroll.tax_baseline_amount', self.tax_baseline_amount)
        params.sudo().set_param('sl_hrm_payroll.regular_holiday_exclude_payroll', self.regular_holiday_exclude_payroll)

    @api.model
    def get_values(self):
        res = super(ResConfigSettings, self).get_values()
        params = self.env['ir.config_parameter']
        tax_baseline_amount = params.sudo().get_param('sl_hrm_payroll.tax_baseline_amount', default=0)
        regular_holiday_exclude_payroll = params.sudo().get_param('sl_hrm_payroll.regular_holiday_exclude_payroll', default=False)

        res.update({
            'tax_baseline_amount': int(tax_baseline_amount) if tax_baseline_amount else 0,
            'regular_holiday_exclude_payroll': regular_holiday_exclude_payroll,
        })
        return res
