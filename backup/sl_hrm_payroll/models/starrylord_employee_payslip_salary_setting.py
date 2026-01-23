import datetime

from odoo import api, fields, models
from odoo.exceptions import ValidationError


class StarryLordEmployeePayslipSalarySetting(models.Model):
    _name = 'starrylord.employee.payslip.salary.setting'
    _description = '本薪變化'

    hr_payslip_id = fields.Many2one('hr.payslip', string='薪資單', ondelete='cascade')
    start_date = fields.Date(string='開始日期')
    end_date = fields.Date(string='結束日期')
    employee_id = fields.Many2one('hr.employee', string='員工', required=True)
    amount = fields.Integer(string='月薪')
    hour_amount = fields.Float(string='時薪')

    def name_get(self):
        result = []
        for grade in self:
            name = str(grade.employee_id.name)
            result.append((grade.id, name))
        return result
