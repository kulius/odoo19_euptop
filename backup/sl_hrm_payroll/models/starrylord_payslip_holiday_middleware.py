from odoo import models, api, fields


class StarryLordPayslipHolidayMiddleware(models.Model):
    _name = 'starrylord.payslip.holiday.middleware'
    _description = '請假明細'

    payslip_id = fields.Many2one('hr.payslip', string='薪資單', ondelete='cascade')
    employee_id = fields.Many2one('hr.employee.public', string='員工')
    start_day = fields.Date(string='開始日期')
    holiday_total_time = fields.Float(string='總時數')
    holiday_apply_id = fields.Many2one('starrylord.holiday.apply', string='請假單')
    holiday_type_id = fields.Many2one('starrylord.holiday.type', string='休假類型')
