# -*- coding: utf-8 -*-
from odoo import models, fields, api


class HrAttendanceRaw(models.Model):
    _name = 'hr.attendance.raw'
    _description = '原始打卡記錄'
    _order = 'check_time desc'
    _rec_name = 'employee_id'

    employee_id = fields.Many2one('hr.employee', string='員工', required=True, index=True, ondelete='cascade')
    employee_number = fields.Char(string='工號', related='employee_id.employee_number', store=True, readonly=True)
    department_id = fields.Many2one('hr.department', string='部門', related='employee_id.department_id', store=True, readonly=True)
    check_time = fields.Datetime(string='打卡時間', required=True, index=True)
    source = fields.Selection([
        ('manual', '手動匯入'),
        ('device', '打卡機'),
        ('system', '系統建立'),
    ], string='來源', default='manual')
    note = fields.Char(string='備註')
    
    _sql_constraints = [
        ('unique_employee_source_check_time', 'unique(employee_id, source, check_time)',
         '同一員工、同一來源不能有相同的打卡時間！'),
    ]
    
    def name_get(self):
        result = []
        for record in self:
            name = f"{record.employee_id.name} - {record.check_time.strftime('%Y-%m-%d %H:%M:%S')}"
            result.append((record.id, name))
        return result
