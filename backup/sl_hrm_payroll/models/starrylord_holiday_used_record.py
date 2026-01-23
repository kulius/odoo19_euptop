from odoo import models, fields


class StarryLordHolidayUsedRecordInherit(models.Model):
    _inherit = 'starrylord.holiday.used.record'
    payslip_id = fields.Many2one('hr.payslip', string='薪資單', ondelete='cascade')
    # payslip_overtime_holiday_middleware_id = fields.Many2one('starrylord.payslip.overtime.holiday.middleware', string='薪資單-加班補休明細', ondelete='cascade')