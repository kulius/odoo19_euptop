from odoo import models, fields


class HrLaborPensionGap(models.Model):
    _name = "hr.labor.pension.gap"
    _description = "勞退級距"

    year = fields.Char(string='年度', required=True, groups="hr.group_hr_user", default=False)
    insurance_level = fields.Integer(string='級距', groups="hr.group_hr_user", required=True, default=False)
    insurance_salary = fields.Float(string='金額', groups="hr.group_hr_user", required=True, default=False)

    def _compute_display_name(self):
        for record in self:
            record.display_name = str("{:,.0f}".format(record.insurance_salary))
