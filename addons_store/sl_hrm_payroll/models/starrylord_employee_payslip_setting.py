from odoo import models, fields, api
import datetime


class StarryLordEmployeePayslipSetting(models.Model):
    _name = 'starrylord.employee.payslip.setting'
    _description = "員工薪資設定"

    employee_id = fields.Many2one('hr.employee', string='員工')
    salary_rule_id = fields.Many2one(
        'hr.salary.rule',
        string='薪資規則',
        domain="[('id', 'in', available_rule_ids)]"
    )

    start_date = fields.Date(
        string='開始日期', default=datetime.date.today(), required=True)
    # 異動日期
    change_date = fields.Date(string='異動日期', default=datetime.date.today())
    change_reason = fields.Char(string='異動原因')
    # 薪資金額
    salary_amount = fields.Float(string='薪資金額')
    # 是否為本薪
    is_basic_wage = fields.Boolean(
        string='是否為本薪', related="salary_rule_id.is_basic")
    
    available_rule_ids = fields.Many2many(
        'hr.salary.rule',
        compute='_compute_available_rule_ids',
        string='可用薪資規則',
        store=True
    )
    
    @api.depends('employee_id')
    def _compute_available_rule_ids(self):
        for rec in self:
            rec.available_rule_ids = False
            structure = rec.employee_id.payroll_structure_id
            if structure:
                rec.available_rule_ids = structure.rule_ids