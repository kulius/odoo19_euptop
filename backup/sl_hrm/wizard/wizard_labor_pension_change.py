from odoo import api, fields, models


class WizardLaborPensionChange(models.TransientModel):
    _name = 'wizard.labor.pension.change'
    _description = '退休金異動'
    start_date = fields.Date(string='生效日期', required=True)

    change_reason_selection = fields.Selection([('add', '加保'), ('off', '退保'), ('promote', '調薪'), ('self_contribution', '自提')],
                                               string='退休金異動原因', default='add')
    self_reimbursement_of_labor_pension = fields.Selection([('0.00', '0%'),
                                                            ('0.01', '1%'),
                                                            ('0.02', '2%'),
                                                            ('0.03', '3%'),
                                                            ('0.04', '4%'),
                                                            ('0.05', '5%'),
                                                            ('0.06', '6%')], string='勞退自提比例', default='0.00')
    comp_reimbursement_of_labor_pension = fields.Selection([('0.00', '0%'),
                                                            ('0.01', '1%'),
                                                            ('0.02', '2%'),
                                                            ('0.03', '3%'),
                                                            ('0.04', '4%'),
                                                            ('0.05', '5%'),
                                                            ('0.06', '6%')], string='勞退公司提撥比例', default='0.06')

    labor_pension_gap_id = fields.Many2one('hr.labor.pension.gap', string='勞退級距')

    @api.model
    def default_get(self, fields):
        res = super(WizardLaborPensionChange, self).default_get(fields)
        setting = self.env['ir.config_parameter'].sudo()
        default_rate = setting.get_param('default_labor_pension_comp_rate', default='0.06')
        res.update({
            'comp_reimbursement_of_labor_pension': default_rate or '0.06',
        })
        return res

    def add(self):
        employee_id = self.env.context.get('active_id')

        if self.change_reason_selection:
            self.env['hr.labor.pension.history'].create(
                {'start_date': self.start_date, 'change_date': fields.Datetime.now(),
                 'change_reason_selection': self.change_reason_selection,
                 'labor_pension_gap_id': self.labor_pension_gap_id.id,
                 'labor_pension_salary': self.labor_pension_gap_id.insurance_salary,
                 'self_reimbursement_of_labor_pension': self.self_reimbursement_of_labor_pension,
                 'comp_reimbursement_of_labor_pension': self.comp_reimbursement_of_labor_pension,
                 'employee_id': employee_id})

            # # 查詢異動歷程中, 日期最接近系統日期的資料代表已生效資料, 更新勞退級距
            # insurance_history = self.env['hr.labor.pension.history'].search(
            #     [('employee_id', '=', employee_id), ('start_date', '<=', fields.Date.today())],
            #     order='start_date desc', limit=1)
            # # 如果labor_insurance_history有資料就要更新健保級距
            # if insurance_history:
            #     if insurance_history.change_reason_selection in ['add', 'promote', 'self_contribution']:
            #         self.env['hr.employee'].browse(employee_id).sudo().write(
            #             {'labor_pension_gap_id': insurance_history.labor_pension_gap_id.id})
            #     else:
            #         self.env['hr.employee'].browse(employee_id).sudo().write(
            #             {'labor_pension_gap_id': False})
            # else:
            #     self.env['hr.employee'].browse(employee_id).sudo().write(
            #         {'labor_pension_gap_id': False})

