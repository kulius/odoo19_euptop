from odoo import api, fields, models


class HrLaborHarmInsuranceGap(models.Model):
    _name = "hr.labor.harm.insurance.gap"
    _description = "勞工職業災害保險級距"

    year = fields.Char(string='年度', required=True, groups="hr.group_hr_user", default=False)
    insurance_level = fields.Integer(string='級距', groups="hr.group_hr_user", required=True, default=False)
    insurance_salary = fields.Float(string='金額', groups="hr.group_hr_user", required=True, default=False)

    # 被保險人負擔金額
    employee_pay = fields.Integer(string='勞工負擔金額', groups="hr.group_hr_user", default=False)

    # 投保單位負擔金額
    company_pay = fields.Integer(string='投保單位負擔金額', groups="hr.group_hr_user", default=False)

    def _compute_display_name(self):
        for record in self:
            record.display_name = str("{:,.0f}".format(record.insurance_salary))
