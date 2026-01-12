from odoo import models, api, fields


class StarryLordPayslipOvertimeHolidayMiddleware(models.Model):
    _name = 'starrylord.payslip.overtime.holiday.middleware'
    _description = '加班補休明細'

    payslip_id = fields.Many2one('hr.payslip', string='薪資單', ondelete='cascade')

    employee_id = fields.Many2one('hr.employee.public', string='員工')
    date_from = fields.Date(string='申請日期')
    days_no_tmp = fields.Float('總時數')
    overtime_type_id = fields.Many2one('starrylord.overtime.type', string="加班類型")
    rate = fields.Float(string='加班費率')
    # allocation_id = fields.Many2one('starrylord.holiday.allocation', string="補休分配")
    # overtime_apply_id = fields.Many2one('starrylord.overtime.apply', string="加班申請")
    # used_record_id = fields.Many2one(comodel_name='starrylord.holiday.used.record',
    #                                  inverse_name='payslip_overtime_middleware_id', string='休假使用紀錄')
