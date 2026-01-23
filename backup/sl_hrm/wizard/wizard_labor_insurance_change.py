from odoo import api, fields, models


class WizardLaborInsuranceChange(models.TransientModel):
    _name = 'wizard.labor.insurance.change'
    _description = '勞保異動'
    start_date = fields.Date(string='生效日期', required=True)

    # 勞保
    change_reason_selection_labor_insurance = fields.Selection([('add', '加保'), ('off', '退保'), ('promote', '調薪')],
                                                               string='勞保異動原因', default='add')
    labor_rate = fields.Selection([('1', '無補助'), ('0.75', '補助1/4'), ('0.5', '補助1/2'), ('0', '免繳')],
                                  string='政府補助勞保費身分別', default='1')
    labor_identity = fields.Selection(
        [('normal', '一般勞工'), ('only_accident', '僅參加就業保險'), ('no_accident', '不參加就業保險')]
        , string='勞工身分', default='normal')
    labor_insurance_gap_id = fields.Many2one('hr.labor.insurance.gap', string='勞保級距')

    def add(self):
        user_id = self.env.context.get('active_id')

        if self.change_reason_selection_labor_insurance:
            self.env['hr.labor.insurance.history'].create(
                {'start_date': self.start_date, 'change_date': fields.Datetime.now(),
                 'change_reason_selection': self.change_reason_selection_labor_insurance,
                 'labor_insurance_gap_id': self.labor_insurance_gap_id.id,
                 'labor_insurance_gap': self.labor_insurance_gap_id.insurance_salary,
                 'labor_rate': self.labor_rate,
                 'labor_identity': self.labor_identity,
                 'labor_insurance_history_id': user_id})
            # 查詢異動歷程中, 日期最接近系統日期的資料代表已生效資料, 更新勞保級距
            labor_insurance_history = self.env['hr.labor.insurance.history'].search(
                [('labor_insurance_history_id', '=', user_id), ('start_date', '<=', fields.Date.today())],
                order='start_date desc', limit=1)
            # 如果labor_insurance_history有資料就要更新健保級距
            if labor_insurance_history:
                if labor_insurance_history.change_reason_selection in ['add', 'promote']:
                    self.env['hr.employee'].browse(user_id).sudo().write(
                        {'hr_labor_insurance_gap_id': labor_insurance_history.labor_insurance_gap_id.id})
                else:
                    self.env['hr.employee'].browse(user_id).sudo().write(
                        {'hr_labor_insurance_gap_id': False})
