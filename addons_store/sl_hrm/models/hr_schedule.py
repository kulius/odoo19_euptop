from odoo import api, fields, models
from datetime import datetime, timedelta, time, date
import logging
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class HrSchedule(models.Model):
    _name = 'hr.schedule'
    _description = '班別'

    name = fields.Char(string='名稱')
    is_user_personal_calendar = fields.Boolean(string="依個人班表及行事歷", default=False)
    is_control_personal_calendar = fields.Boolean(string="是否依【班表】計算-請休假時間", default=False)
    worktime_ids = fields.One2many('hr.schedule.worktime', 'worktime_id', string='工作時間')

    def convert_float_time_to_string(self, time_float):
        if time_float is None:
            return None
        hours = int(time_float)
        minutes = int((time_float - hours) * 60)
        return f"{hours:02d}:{minutes:02d}"

    def calc_personal_calendar_time(self, employee_id, request_from, request_to):
        # 依固定班表計算
        holiday_model = self.env['hr.public.holiday']
        overlapping_holidays = holiday_model.sudo().is_duraction_has_holiday(request_from, request_to)
        if not employee_id.schedule_id.is_user_personal_calendar:
            start = request_from
            end = request_to
            # Calculate the total leave hours
            total_leave_hours = 0
            current = start
            while current < end:
                worktime = self.env['hr.schedule.worktime'].sudo().search(
                    [('worktime_id', '=', employee_id.schedule_id.id),
                     ('date_type', '=', 'schedule'),
                     ('dayofweek', '=', current.weekday()),
                     ])
                if worktime:
                    # 你需要将 float 时间转换为 'HH:MM' 格式的字符串
                    am_start_time = self.convert_float_time_to_string(worktime.am_start)
                    am_end_time = self.convert_float_time_to_string(worktime.am_end)
                    pm_start_time = self.convert_float_time_to_string(worktime.pm_start)
                    pm_end_time = self.convert_float_time_to_string(worktime.pm_end)
                    # 添加上午和下午的工作时间
                    shifts = []
                    if worktime.am_start is not None and worktime.am_end is not None:
                        shifts.append((am_start_time, am_end_time))
                    if worktime.pm_start is not None and worktime.pm_end is not None:
                        shifts.append((pm_start_time, pm_end_time))

                    if shifts:
                        for shift in shifts:
                            work_start_str, work_end_str = shift
                            work_start = datetime.combine(current.date(),
                                                          datetime.strptime(work_start_str, "%H:%M").time())
                            work_end = datetime.combine(current.date(), datetime.strptime(work_end_str, "%H:%M").time())

                            # Calculate leave hours within the work shift
                            if work_start < end < work_end:
                                total_leave_hours += (end - max(start, work_start)).seconds / 3600
                            elif work_start < start < work_end:
                                total_leave_hours += (min(end, work_end) - start).seconds / 3600
                            elif start <= work_start and work_end <= end:
                                total_leave_hours += (work_end - work_start).seconds / 3600

                            if overlapping_holidays:
                                # 當請假時間遇到設定的公眾假日，要把請假時數扣掉
                                overlapping_start = work_start
                                overlapping_end = work_end
                                if work_start < end < work_end:
                                    overlapping_start = max(start, work_start)
                                    overlapping_end = end
                                elif work_start < start < work_end:
                                    overlapping_start = start
                                    overlapping_end = min(end, work_end)
                                elif ((start < work_start and end <= work_start)
                                        or (start >= work_end and end > work_end)):
                                    continue
                                current_time = overlapping_start
                                while current_time < overlapping_end:
                                    interval_end = current_time + timedelta(minutes=15)
                                    in_holiday = overlapping_holidays.search([
                                        ('start_date', '<=', current_time),
                                        ('end_date', '>=', interval_end),
                                        ('holiday_type', '!=', 'make_up_day')
                                    ], limit=1)
                                    if in_holiday:
                                        total_leave_hours -= 0.25
                                    current_time = interval_end
                        _logger.info(f"total_leave_hours: {total_leave_hours}")

                # Move to the next day
                current += timedelta(days=1)
                current = current.replace(hour=0, minute=0, second=0, microsecond=0)

            return total_leave_hours

        else:
            start = request_from
            end = request_to
            # Calculate the total leave hours
            total_leave_hours = 0
            current = start
            while current < end:
                worktime = self.env['hr.personal.calendar'].sudo().search(
                    [('employee_id', '=', employee_id.id),
                     ('date_type', '=', 'schedule'),
                     ('calendar_date', '=', current), ])
                if worktime:
                    # 你需要将 float 时间转换为 'HH:MM' 格式的字符串
                    am_start_time = worktime.up_start + timedelta(hours=8)
                    am_end_time = worktime.up_end + timedelta(hours=8)
                    pm_start_time = worktime.down_start + timedelta(hours=8)
                    pm_end_time = worktime.down_end + timedelta(hours=8)
                    # 添加上午和下午的工作时间
                    shifts = []
                    if worktime.up_start and worktime.up_end:
                        shifts.append((am_start_time, am_end_time))
                    if worktime.down_start and worktime.down_end:
                        shifts.append((pm_start_time, pm_end_time))

                    if shifts:
                        for shift in shifts:
                            work_start, work_end = shift

                            # Calculate leave hours within the work shift
                            if work_start < end < work_end:
                                total_leave_hours += (end - max(start, work_start)).seconds / 3600
                            elif work_start < start < work_end:
                                total_leave_hours += (min(end, work_end) - start).seconds / 3600
                            elif start <= work_start and work_end <= end:
                                total_leave_hours += (work_end - work_start).seconds / 3600

                            if overlapping_holidays:
                                overlapping_start = work_start
                                overlapping_end = work_end
                                if work_start < end < work_end:
                                    overlapping_start = max(start, work_start)
                                    overlapping_end = end
                                elif work_start < start < work_end:
                                    overlapping_start = start
                                    overlapping_end = min(end, work_end)
                                elif ((start < work_start and end <= work_start)
                                        or (start >= work_end and end > work_end)):
                                    continue
                                current_time = overlapping_start
                                while current_time < overlapping_end:
                                    interval_end = current_time + timedelta(minutes=15)
                                    in_holiday = overlapping_holidays.search([
                                        ('start_date', '<=', current_time),
                                        ('end_date', '>=', interval_end),
                                        ('holiday_type', '!=', 'make_up_day')
                                    ], limit=1)
                                    if in_holiday:
                                        total_leave_hours -= 0.25
                                    current_time = interval_end
                # Move to the next day
                current += timedelta(days=1)
                current = current.replace(hour=0, minute=0, second=0, microsecond=0)

            return total_leave_hours


class HrScheduleWorktime(models.Model):
    _name = 'hr.schedule.worktime'
    _description = '班別工作時間明細'

    worktime_id = fields.Many2one('hr.schedule', 'worktime_ids')
    name = fields.Char(string='名稱')
    date_type = fields.Selection([('schedule', '排班'), ('overtime', '加班'), ('leave', '請假'), ('no_work', '空班'),
                                  ('holiday', '國定假日'), ('day_off', '休假日'), ('regular_holiday', '例假日')],
                                 string='類型',
                                 default='schedule')
    type = fields.Char(string='分類')
    time_type = fields.Many2one(comodel_name="hr.schedule.time.type", string="排班代號", required=False)
    dayofweek = fields.Selection(
        [('0', '周一'), ('1', '周二'), ('2', '周三'), ('3', '周四'), ('4', '周五'), ('5', '周六'),
         ('6', '周日')], string='星期')
    work_start = fields.Float(string='開始時間')
    work_end = fields.Float(string='結束時間')
    am_start = fields.Float(string='上午開始時間')
    am_end = fields.Float(string='上午結束時間')
    pm_start = fields.Float(string='下午開始時間')
    pm_end = fields.Float(string='下午結束時間')

    sequence = fields.Integer(default=10)

    _sql_constraints = [
        ('unique_dayofweek', 'unique(worktime_id, dayofweek)', '同一班別中，星期不能重複!')
    ]

    @api.onchange('time_type')
    def onchange_time_type(self):
        if self.time_type:
            self.work_start = self.time_type.work_start
            self.work_end = self.time_type.work_end
            self.am_start = self.time_type.am_start
            self.am_end = self.time_type.am_end
            self.pm_start = self.time_type.pm_start
            self.pm_end = self.time_type.pm_end

    def copy_day(self):
        self.ensure_one()
        values = {
            'worktime_id': self.worktime_id.id,
            'name': '',
            'type': self.type,
            'time_type': self.time_type.id,
            'dayofweek': str(int(self.dayofweek) + 1),
            'work_start': self.work_start,
            'work_end': self.work_end,
            'am_start': self.am_start,
            'am_end': self.am_end,
            'pm_start': self.pm_start,
            'pm_end': self.pm_end,
            'sequence': self.sequence + 1
        }
        self.create(values)

    @api.model
    def create(self, vals):
        if not vals.get('name'):
            weekStr = '周一 周二 周三 周四 周五 周六 周日 '
            time_seconds_start = int(vals.get('work_start', 0) * 3600)
            time_obj_start = time(hour=(time_seconds_start // 3600), minute=(time_seconds_start % 3600) // 60)
            time_seconds_end = int(vals.get('work_end', 0) * 3600)
            time_obj_end = time(hour=(time_seconds_end // 3600), minute=(time_seconds_end % 3600) // 60)
            weekid = int(vals.get('dayofweek', 0)) * 3
            vals['name'] = weekStr[weekid: weekid + 3] + time_obj_start.strftime('%H:%M') + '-' + time_obj_end.strftime(
                '%H:%M')
        return super(HrScheduleWorktime, self).create(vals)
