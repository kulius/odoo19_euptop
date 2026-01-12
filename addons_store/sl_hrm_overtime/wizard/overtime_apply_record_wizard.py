# models/holiday_used_record_wizard.py
from odoo import models, fields
from datetime import date
import calendar

class OvertimeApplyRecordWizard(models.TransientModel):
    _name = 'overtime.apply.record.wizard'
    _description = '加班申請紀錄查詢精靈'

    start_date = fields.Date(string="開始日期", required=True,
        default=lambda self: date.today().replace(day=1))
    end_date = fields.Date(string="結束日期", 
        required=True,default=lambda self: date.today().replace(
        day=calendar.monthrange(date.today().year, date.today().month)[1]))
    
    state = fields.Selection([('f_approve', '待核准'),
                                ('agree', '確認執行'),
                                ('refused', '己拒絕'),
                                ('all', '所有'),],
                                string="簽核狀態",
                                default="agree",
                                required=True,)
    def set_this_month(self):
        for rec in self:
            today = date.today()
            rec.start_date = today.replace(day=1)
            rec.end_date = today.replace(
                day=calendar.monthrange(today.year, today.month)[1]
            )
        return self.reopen_wizard()

    def set_this_year(self):
        for rec in self:
            today = date.today()
            rec.start_date = date(today.year, 1, 1)
            rec.end_date = date(today.year, 12, 31)
        return self.reopen_wizard()
    
    def reopen_wizard(self):
        return {
            'type': 'ir.actions.act_window',
            'name': '加班申請紀錄查詢',
            'res_model': 'overtime.apply.record.wizard',
            'view_mode': 'form',
            'res_id': self.id,
            'target': 'new',
        }       
    
    def action_open_pivot(self):
        domain = [
            ('start_day', '>=', self.start_date),
            ('start_day', '<=', self.end_date),
        ]
        if self.state != 'all':
            domain.append(('state', '=', self.state))
        return {
            'type': 'ir.actions.act_window',
            'name': '加班申請紀錄表',
            'res_model': 'starrylord.overtime.apply',
            'view_mode': 'pivot',
            'view_id': self.env.ref('sl_hrm_overtime.starrylord_overtime_apply_pivot').id,
            'target': 'current',
            'domain': domain,
        }
