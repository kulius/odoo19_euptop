from odoo import models, api, fields


class StarryLordPayslipOvertimeMiddleware(models.Model):
    _name = 'starrylord.payslip.overtime.middleware'
    _description = '加班明細'

    payslip_id = fields.Many2one('hr.payslip', string='薪資單', ondelete='cascade')

    employee_id = fields.Many2one('hr.employee.public', string='員工')
    date_from = fields.Date(string='申請日期')
    # request_from = fields.Many2one('time.select.setting', store=True, string='開始時間')
    days_no_tmp = fields.Float('總時數')
    type = fields.Selection([('cash', '現金'), ('holiday', '補休')], default="holiday", string="假別")
    overtime_type_id = fields.Many2one('starrylord.overtime.type', string="加班類型")
    overtime_apply_id = fields.Many2one('starrylord.overtime.apply', string="加班申請")
    used_record_id = fields.Many2one(comodel_name='starrylord.holiday.used.record',
                                     inverse_name='payslip_overtime_middleware_id', string='休假使用紀錄')
