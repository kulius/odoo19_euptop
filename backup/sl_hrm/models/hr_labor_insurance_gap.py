from odoo import api, fields, models


class HrLaborInsuranceGap(models.Model):
    _name = "hr.labor.insurance.gap"
    _description = "勞保級距"
    _order = 'year desc, insurance_level asc'

    year = fields.Char(string='年度', required=True, groups="hr.group_hr_user", default=False)
    insurance_level = fields.Integer(string='保險級別', groups="hr.group_hr_user", required=True, default=False)
    insurance_salary = fields.Float(string='保險金額', groups="hr.group_hr_user", required=True, default=False)

    # 被保險人負擔金額
    employee_pay = fields.Integer(string='勞工負擔金額', groups="hr.group_hr_user", default=False)

    # 投保單位負擔金額
    company_pay = fields.Integer(string='投保單位負擔金額', groups="hr.group_hr_user", default=False)

    is_labor = fields.Boolean(string='勞保', default=False)

    def _compute_display_name(self):
        for record in self:
            record.display_name = str("{:,.0f}".format(record.insurance_salary))