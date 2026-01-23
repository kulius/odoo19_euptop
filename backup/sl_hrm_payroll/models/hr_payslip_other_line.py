# Part of Odoo. See LICENSE file for full copyright and licensing details.
import datetime
from odoo import _, api, fields, models
from odoo.exceptions import UserError
from dateutil.relativedelta import relativedelta


class HrPayslipOtherLine(models.Model):
    _name = "hr.payslip.other.line"
    _description = "他項薪資項目"

    payslip_id = fields.Many2one(comodel_name="hr.payslip", string="薪資單", required=True, ondelete="cascade")
    salary_rule_id = fields.Many2one(
        comodel_name="hr.salary.rule", 
        string="規則", 
        required=True,
        domain="[('company_id', '=', company_id)]"
    )
    company_id = fields.Many2one(
        comodel_name="res.company", 
        string="公司", 
        default=lambda self: self.env.company,
        invisible=True,
    )

    amount = fields.Integer(digits="Payroll", string='金額')
    quantity = fields.Float(digits="Payroll", default=1.0)
    total = fields.Float(

        string="合計",
        digits="Payroll",
        store=True,
    )

    infrequent = fields.Boolean(string='非經常性薪資', default=False)
    # 原繼承於hr_salary_rule
    category_id = fields.Many2one(
        "hr.salary.rule.category", related="salary_rule_id.category_id", string="類別", required=True
    )
    name = fields.Char(string='名稱', required=True, store=True)
    source = fields.Char(string='來源', compute='compute_source', store=True, readonly=False)
    code = fields.Char(
        required=True,
        help="薪資規則的代碼可以被其他規則的計算公式使用。這樣的話，它是區分大小寫的。",
        string='代碼',
        related='salary_rule_id.code',
    )

    note = fields.Char(string="備註", stroe=True)

    @api.constrains('amount')
    def check_amount(self):
        for rec in self:
            if rec.amount < 0:
                raise UserError('不可輸入負數')

    @api.onchange('salary_rule_id')
    def onchange_salary_rule_id(self):
        self.ensure_one()
        self.category_id = self.salary_rule_id.category_id
