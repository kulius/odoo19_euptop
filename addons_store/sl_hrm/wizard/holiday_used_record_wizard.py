# models/holiday_used_record_wizard.py
from odoo import models, fields
from datetime import date
import calendar

class HolidayUsedRecordWizard(models.TransientModel):
    _name = 'holiday.used.record.wizard'
    _description = '休假使用紀錄查詢精靈'

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
            'name': '休假紀錄報表查詢',
            'res_model': 'holiday.used.record.wizard',
            'view_mode': 'form',
            'res_id': self.id,
            'target': 'new',
        }       
    
    def action_open_pivot(self):
        domain = [
            ('holiday_day', '>=', self.start_date),
            ('holiday_day', '<=', self.end_date),
        ]
        if self.state != 'all':
            domain.append(('holiday_apply_id.state', '=', self.state))
        return {
            'type': 'ir.actions.act_window',
            'name': '休假使用紀錄表',
            'res_model': 'starrylord.holiday.used.record',
            'view_mode': 'pivot',
            'target': 'current',
            'domain': domain,
            'context': {
                'search_default_group_by_employee_id': 1,
                'search_default_group_by_holiday_allocation_id': 1,
            }
        }
