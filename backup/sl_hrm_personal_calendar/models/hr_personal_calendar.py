from odoo import models, fields, api
from dateutil.relativedelta import relativedelta
from datetime import datetime, time, date
import datetime


class HrPersonalCalendar(models.Model):
    _name = 'hr.personal.calendar'
    _description = '個人排班及行事曆'
    _inherit = ["mail.thread"]
    _rec_name = "display_name"
    user_id = fields.Many2one('res.users', string='User', related='employee_id.user_id', related_sudo=True,
                              compute_sudo=True, store=True, readonly=True)
    employee_id = fields.Many2one('hr.employee.public', string='員工姓名')
    department_id = fields.Many2one('hr.department', string="部門",
                                    related="employee_id.department_id", store=True)
    date_type = fields.Selection([('schedule', '排班'), ('overtime', '加班'), ('leave', '請假'), ('no_work', '空班'),
                                  ('holiday', '國定假日'), ('day_off', '休假日'), ('regular_holiday', '例假日')],
                                 string='類型', default='schedule')
    type = fields.Char(string='分類')
    schedule_id = fields.Many2one(comodel_name="hr.schedule", string="班別", required=False, )
    time_type_id = fields.Many2one(comodel_name="hr.schedule.time.type", string="排班代號", required=False, )
    calendar_date = fields.Date(string='日期', default=fields.Date.today())
    hour_from = fields.Many2one('starrylord.holiday.hour.list', string='開始時間(時)', domain=[('is_select', '=', True)])
    min_from = fields.Many2one('starrylord.holiday.min.list', string='開始時間(分)', domain=[('is_select', '=', True)])
    hour_to = fields.Many2one('starrylord.holiday.hour.list', string='結束時間(時)', domain=[('is_select', '=', True)])
    min_to = fields.Many2one('starrylord.holiday.min.list', string='結束時間(分)', domain=[('is_select', '=', True)])

    start_date = fields.Datetime(string='開始時間')
    end_date = fields.Datetime(string='結束時間')
    am_start = fields.Datetime(string='上午開始時間')
    am_end = fields.Datetime(string='上午結束時間')
    pm_start = fields.Datetime(string='下午開始時間')
    pm_end = fields.Datetime(string='下午結束時間')


    display_name = fields.Char(compute='_compute_display_name', store=False, invisible=True)

    @api.onchange('calendar_date', 'time_type_id')
    def onchange_calendar_date(self):
        if self.time_type_id:
            self.start_date = self.merge_date_time(self.calendar_date, self.time_type_id.work_start)
            self.end_date = self.merge_date_time(self.calendar_date, self.time_type_id.work_end)
            self.am_start = self.merge_date_time(self.calendar_date, self.time_type_id.am_start)
            self.am_end = self.merge_date_time(self.calendar_date, self.time_type_id.am_end)
            self.pm_start = self.merge_date_time(self.calendar_date, self.time_type_id.pm_start)
            self.pm_end = self.merge_date_time(self.calendar_date, self.time_type_id.pm_end)

    def merge_date_time(self, date_field, time_field):
        # 當24至遇到24時直接加一天
        if time_field == 24:
            time_field = 0
            date_field += relativedelta(days=+1)
        # 將時間小數點轉成 time 物件
        if type(time_field) != 'time':
            time_seconds = int(time_field * 3600)
            time_obj = time(hour=(time_seconds // 3600), minute=(time_seconds % 3600) // 60, second=(time_seconds % 60))
        else:
            time_obj = time_field
        # 將日期和時間合併成 datetime 物件
        datetime_obj = datetime.datetime.combine(date_field, time_obj)
        # 時區校正
        datetime_obj -= datetime.timedelta(hours=8)

        return datetime_obj

    def _compute_display_name(self):
        date_type_str = ''
        result = []
        for grade in self:
            if grade.date_type == 'schedule':
                date_type_str = '排班'
            elif grade.date_type == 'overtime':
                date_type_str = '加班'
            elif grade.date_type == 'leave':
                date_type_str = '請假'
            elif grade.date_type == 'day_off':
                date_type_str = '休假日'
            elif grade.date_type == 'regular_holiday':
                date_type_str = '例假日'
            elif grade.date_type == 'holiday':
                date_type_str = '國定假日'
            elif grade.date_type == 'no_work':
                date_type_str = '空班'
            name = "%s %s" % (grade.employee_id.name, date_type_str)
            grade.display_name = name


