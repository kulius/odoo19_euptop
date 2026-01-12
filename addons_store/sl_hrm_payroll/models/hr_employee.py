from odoo import models, fields, api
from odoo.exceptions import ValidationError, UserError


class HrEmployeeInheritancePayroll(models.Model):
    _inherit = "hr.employee"

    payroll_structure_id = fields.Many2one('hr.payroll.structure', string='薪資結構')

    # 薪資設定
    payslip_setting_ids = fields.One2many('starrylord.employee.payslip.setting', 'employee_id', string='薪資設定')

    is_payslip_compute = fields.Boolean(string='此員工正在計算薪資', default=False)

    def action_generate_salary_rules(self):
        """
        根據所選薪資結構生成對應的薪資規則
        """
        for employee in self:
            if not employee.payroll_structure_id:
                raise UserError('請先選擇薪資結構！')

            salary_rules = self.env['hr.salary.rule'].search([
                ('id', 'in', employee.payroll_structure_id.rule_ids.ids),
            ])
            if not salary_rules:
                raise UserError('未找到對應的薪資規則！')

            existing_rule_ids = employee.payslip_setting_ids.mapped('salary_rule_id.id')

            # 找到現有紀錄中最早的開始日期
            existing_start_dates = employee.payslip_setting_ids.mapped('start_date')
            earliest_start_date = min(existing_start_dates) if existing_start_dates else fields.Date.today()

            # 篩選出尚未存在於員工設定中的規則
            new_rules = salary_rules.filtered(lambda rule: rule.id not in existing_rule_ids and rule.amount_select == 'fix')

            new_records = [(0, 0, {
                'salary_rule_id': rule.id,
                'start_date': earliest_start_date,
                'salary_amount': 0.0
            }) for rule in new_rules]

            # 更新員工的薪資設定
            employee.payslip_setting_ids = new_records