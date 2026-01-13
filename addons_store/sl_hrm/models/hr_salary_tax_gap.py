from odoo import api, fields, models


class HrSalaryGap(models.Model):
    _name = "hr.salary.tax.gap"
    _description = "薪資所得扣繳表"

    start = fields.Integer(string='薪資範圍(起)', groups="hr.group_hr_user", required=True, default=False)
    end = fields.Integer(string='薪資範圍(迄)', groups="hr.group_hr_user", required=True, default=False)
    cost_0 = fields.Integer(string='0', groups="hr.group_hr_user", required=True, default=False)
    cost_1 = fields.Integer(string='1', groups="hr.group_hr_user", required=True, default=False)
    cost_2 = fields.Integer(string='2', groups="hr.group_hr_user", required=True, default=False)
    cost_3 = fields.Integer(string='3', groups="hr.group_hr_user", required=True, default=False)
    cost_4 = fields.Integer(string='4', groups="hr.group_hr_user", required=True, default=False)
    cost_5 = fields.Integer(string='5', groups="hr.group_hr_user", required=True, default=False)
    cost_6 = fields.Integer(string='6', groups="hr.group_hr_user", required=True, default=False)
    cost_7 = fields.Integer(string='7', groups="hr.group_hr_user", required=True, default=False)
    cost_8 = fields.Integer(string='8', groups="hr.group_hr_user", required=True, default=False)
    cost_9 = fields.Integer(string='9', groups="hr.group_hr_user", required=True, default=False)
    cost_10 = fields.Integer(string='10', groups="hr.group_hr_user", required=True, default=False)
    cost_11 = fields.Integer(string='11', groups="hr.group_hr_user", required=True, default=False)

    _sql_constraints = [
        ('unique_start_end', '級距範圍不可重複', ['start', 'end'])
    ]

    def get_cost(self, salary, dependents=0):
        """取得薪資所得扣繳表的費用"""
        if not salary:
            return 0
        record = self.env['hr.salary.tax.gap'].search([
            ('start', '<=', salary),
            ('end', '>=', salary)
        ], limit=1)
        if record:
            return getattr(record, f'cost_{dependents}', 0)
        return 0
