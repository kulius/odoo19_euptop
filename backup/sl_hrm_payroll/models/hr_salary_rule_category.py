from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class HrSalaryRuleCategory(models.Model):
    _name = "hr.salary.rule.category"
    _description = "薪資分類"

    name = fields.Char(string='名稱')
    code = fields.Char(string='代碼')
    parent_id = fields.Many2one(
        "hr.salary.rule.category",
        string="上級",
        help="Linking a salary category to its parent is used only for the "
             "reporting purpose.",
    )
    children_ids = fields.One2many(
        "hr.salary.rule.category", "parent_id", string="Children"
    )
    note = fields.Text(string="便簽")
    company_id = fields.Many2one(
        "res.company",
        string="Company",
        default=lambda self: self.env.company,
    )
