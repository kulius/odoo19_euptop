from odoo import models, fields


class HrHealthInsuranceGap(models.Model):
    _name = "hr.health.insurance.gap"
    _description = "健保級距"
    _order = 'year desc, insurance_level asc'

    year = fields.Char(string='年度', groups="hr.group_hr_user", required=True, default=False)
    insurance_level = fields.Integer(string='保險級別', groups="hr.group_hr_user", required=True, default=False)
    insurance_salary = fields.Float(string='保險金額', groups="hr.group_hr_user", required=True, default=False)

    # 被保險人及眷屬負擔金額
    employee_pay = fields.Integer(string='員工負擔金額', groups="hr.group_hr_user", default=False)

    # 投保單位負擔金額
    company_pay = fields.Integer(string='投保單位負擔金額', groups="hr.group_hr_user", default=False)

    # 政府補助金額
    government_pay = fields.Integer(string='政府補助金額', groups="hr.group_hr_user", default=False)

    # 公司負責人自負金額
    legal_pay = fields.Integer(string='公司負責人自負金額', groups="hr.group_hr_user", default=False)



    def _compute_display_name(self):
        for record in self:
            record.display_name = str("{:,.0f}".format(record.insurance_salary))
