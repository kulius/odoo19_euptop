from odoo import api, fields, models


class WizardLaborHarmInsuranceChange(models.TransientModel):
    _name = 'wizard.labor.harm.insurance.change'
    _description = '勞工職業災害保險異動'
    start_date = fields.Date(string='生效日期', required=True)

    # 勞保
    change_reason_selection = fields.Selection([('add', '加保'), ('off', '退保'), ('promote', '調薪')],
                                               string='異動原因', default='add')
    insurance_gap_id = fields.Many2one('hr.labor.harm.insurance.gap', string='級距')

    def add(self):
        employee_id = self.env.context.get('active_id')

        if self.change_reason_selection:
            self.env['hr.labor.harm.insurance.history'].create(
                {'start_date': self.start_date, 'change_date': fields.Datetime.now(),
                 'change_reason_selection': self.change_reason_selection,
                 'insurance_gap_id': self.insurance_gap_id.id,
                 'insurance_salary': self.insurance_gap_id.insurance_salary,
                 'employee_id': employee_id})
            # 查詢異動歷程中, 日期最接近系統日期的資料代表已生效資料, 更新勞保級距
            insurance_history = self.env['hr.labor.harm.insurance.history'].search(
                [('employee_id', '=', employee_id), ('start_date', '<=', fields.Date.today())],
                order='start_date desc', limit=1)
            # 如果labor_insurance_history有資料就要更新健保級距
            if insurance_history:
                if insurance_history.change_reason_selection in ['add', 'promote']:
                    self.env['hr.employee'].browse(employee_id).sudo().write(
                        {'labor_harm_insurance_gap_id': insurance_history.insurance_gap_id.id})
                else:
                    self.env['hr.employee'].browse(employee_id).sudo().write(
                        {'labor_harm_insurance_gap_id': False})
