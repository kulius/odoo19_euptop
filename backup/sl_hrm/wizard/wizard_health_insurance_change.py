from odoo import api, fields, models


class WizardHealthInsuranceChange(models.TransientModel):
    _name = 'wizard.health.insurance.change'
    _description = '健保異動'
    start_date = fields.Date(string='生效日期', required=True)

    change_reason_selection_health_insurance = fields.Selection([('add', '加保'), ('off', '退保'), ('promote', '調薪')],
                                                                string='健保異動原因', default='add')
    health_rate = fields.Selection([('1', '無補助'), ('0.75', '補助1/4'), ('0.5', '補助1/2'), ('0', '免繳')],
                                   string='政府補助勞保費身分別', default='1')

    health_insurance_gap_id = fields.Many2one('hr.health.insurance.gap', string='健保級距')

    def add(self):
        user_id = self.env.context.get('active_id')

        if self.change_reason_selection_health_insurance:
            self.env['hr.health.insurance.history'].create(
                {'start_date': self.start_date, 'change_date': fields.Datetime.now(),
                 'change_reason_selection': self.change_reason_selection_health_insurance,
                 'health_insurance_gap_id': self.health_insurance_gap_id.id,
                 'health_insurance_gap': self.health_insurance_gap_id.insurance_salary,
                 'health_rate': self.health_rate,
                 'health_insurance_history_id': user_id})
            # 查詢異動歷程中, 日期最接近系統日期的資料代表已生效資料, 更新健保級距
            health_insurance_history = self.env['hr.health.insurance.history'].search(
                [('health_insurance_history_id', '=', user_id), ('start_date', '<=', fields.Date.today())],
                order='start_date desc', limit=1)
            # 如果health_insurance_history有資料就要更新健保級距
            if health_insurance_history:
                if health_insurance_history.change_reason_selection in ['add', 'promote']:
                    self.env['hr.employee'].browse(user_id).sudo().write(
                        {'hr_health_insurance_gap_id': health_insurance_history.health_insurance_gap_id.id})
                else:
                    self.env['hr.employee'].browse(user_id).write(
                        {'hr_health_insurance_gap_id': False})
