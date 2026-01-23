import datetime

from dateutil.relativedelta import relativedelta
from pytz import timezone
from odoo import fields, models, api
from odoo.tools.intervals import Intervals


class StarryLordHrAttendance(models.Model):
    _inherit = "hr.attendance"

    active = fields.Boolean(default=True)
    employee_number = fields.Char(string="員工編號", related="employee_id.employee_number", stored=False)
    employee_department_id = fields.Many2one(comodel_name="hr.department", string="部門",
                                             related="employee_id.department_id"
                                             , stored=False)

    @api.constrains('check_in', 'check_out', 'employee_id')
    def _check_validity(self):
        """ Verifies the validity of the attendance record compared to the others from the same employee.
            For the same employee we must have :
                * maximum 1 "open" attendance record (without check_out)
                * no overlapping time slices with previous employee records
        """
        return True

    def _get_employee_calendar(self):
        self.ensure_one()
        return self.employee_id.resource_calendar_id or self.employee_id.company_id.resource_calendar_id

    # @api.depends('check_in', 'check_out')
    # def _compute_worked_hours(self):
    #     for attendance in self:
    #         if attendance.check_out and attendance.check_in and attendance.employee_id:
    #             tz = timezone(self.env.user.tz)
    #             check_in_tz = attendance.check_in.astimezone(tz)
    #             check_out_tz = attendance.check_out.astimezone(tz)
    #
    #             # 午休時間
    #             lunch_intervals = self._attendance_intervals_batch(
    #                 check_in_tz, check_out_tz, resource, lunch=True)
    #             attendance_intervals = Intervals([(check_in_tz, check_out_tz, attendance)]) #- lunch_intervals[resource.id]
    #             delta = sum((i[1] - i[0]).total_seconds() for i in attendance_intervals)
    #             attendance.worked_hours = delta / 3600.0
    #         else:
    #             attendance.worked_hours = False

    # def _attendance_intervals_batch(self, start_dt, end_dt, resources=None, domain=None, tz=None, lunch=False):
    #     assert start_dt.tzinfo and end_dt.tzinfo
    #     self.ensure_one()
    #     if not resources:
    #         resources = self.env['resource.resource']
    #         resources_list = [resources]
    #     else:
    #         resources_list = list(resources) + [self.env['resource.resource']]
    #     resource_ids = [r.id for r in resources_list]
    #     domain = domain if domain is not None else []
    #     domain = expression.AND([domain, [
    #         ('calendar_id', '=', self.id),
    #         ('resource_id', 'in', resource_ids),
    #         ('display_type', '=', False),
    #         ('day_period', '!=' if not lunch else '=', 'lunch'),
    #     ]])
    #
    #     attendances = self.env['resource.calendar.attendance'].search(domain)
    #     # Since we only have one calendar to take in account
    #     # Group resources per tz they will all have the same result
    #     resources_per_tz = defaultdict(list)
    #     for resource in resources_list:
    #         resources_per_tz[tz or timezone((resource or self).tz)].append(resource)
    #     # Resource specific attendances
    #     attendance_per_resource = defaultdict(lambda: self.env['resource.calendar.attendance'])
    #     # Calendar attendances per day of the week
    #     # * 7 days per week * 2 for two week calendars
    #     attendances_per_day = [self.env['resource.calendar.attendance']] * 7 * 2
    #     weekdays = set()
    #     for attendance in attendances:
    #         if attendance.resource_id:
    #             attendance_per_resource[attendance.resource_id] |= attendance
    #         weekday = int(attendance.dayofweek)
    #         weekdays.add(weekday)
    #         if self.two_weeks_calendar:
    #             weektype = int(attendance.week_type)
    #             attendances_per_day[weekday + 7 * weektype] |= attendance
    #         else:
    #             attendances_per_day[weekday] |= attendance
    #             attendances_per_day[weekday + 7] |= attendance
    #
    #     start = start_dt.astimezone(utc)
    #     end = end_dt.astimezone(utc)
    #     bounds_per_tz = {
    #         tz: (start_dt.astimezone(tz), end_dt.astimezone(tz))
    #         for tz in resources_per_tz.keys()
    #     }
    #     # Use the outer bounds from the requested timezones
    #     for tz, bounds in bounds_per_tz.items():
    #         start = min(start, bounds[0].replace(tzinfo=utc))
    #         end = max(end, bounds[1].replace(tzinfo=utc))
    #     # Generate once with utc as timezone
    #     days = rrule(DAILY, start.date(), until=end.date(), byweekday=weekdays)
    #     ResourceCalendarAttendance = self.env['resource.calendar.attendance']
    #     base_result = []
    #     per_resource_result = defaultdict(list)
    #     for day in days:
    #         week_type = ResourceCalendarAttendance.get_week_type(day)
    #         attendances = attendances_per_day[day.weekday() + 7 * week_type]
    #         for attendance in attendances:
    #             if (attendance.date_from and day.date() < attendance.date_from) or\
    #                 (attendance.date_to and attendance.date_to < day.date()):
    #                 continue
    #             day_from = datetime.combine(day, float_to_time(attendance.hour_from))
    #             day_to = datetime.combine(day, float_to_time(attendance.hour_to))
    #             if attendance.resource_id:
    #                 per_resource_result[attendance.resource_id].append((day_from, day_to, attendance))
    #             else:
    #                 base_result.append((day_from, day_to, attendance))
    #
    #
    #     # Copy the result localized once per necessary timezone
    #     # Strictly speaking comparing start_dt < time or start_dt.astimezone(tz) < time
    #     # should always yield the same result. however while working with dates it is easier
    #     # if all dates have the same format
    #     result_per_tz = {
    #         tz: [(max(bounds_per_tz[tz][0], tz.localize(val[0])),
    #             min(bounds_per_tz[tz][1], tz.localize(val[1])),
    #             val[2])
    #                 for val in base_result]
    #         for tz in resources_per_tz.keys()
    #     }
    #     result_per_resource_id = dict()
    #     for tz, resources in resources_per_tz.items():
    #         res = result_per_tz[tz]
    #         res_intervals = Intervals(res)
    #         for resource in resources:
    #             if resource in per_resource_result:
    #                 resource_specific_result = [(max(bounds_per_tz[tz][0], tz.localize(val[0])), min(bounds_per_tz[tz][1], tz.localize(val[1])), val[2])
    #                     for val in per_resource_result[resource]]
    #                 result_per_resource_id[resource.id] = Intervals(itertools.chain(res, resource_specific_result))
    #             else:
    #                 result_per_resource_id[resource.id] = res_intervals
    #     return result_per_resource_id

class HrEmployeeInherit(models.Model):
    _inherit = "hr.employee"

    is_no_need_check_in = fields.Boolean(
        string='無需打卡',
        readonly=True
    )
    employee_number = fields.Char(string="員工編號", stored=False)
    attendance_ids = fields.One2many(
        'hr.attendance', 'employee_id', groups="hr_attendance.group_hr_attendance_user,hr.group_hr_user")
    last_attendance_id = fields.Many2one(
        'hr.attendance', compute='_compute_last_attendance_id', store=True,
        groups="hr_attendance.group_hr_attendance_kiosk,hr_attendance.group_hr_attendance,hr.group_hr_user")
    attendance_state = fields.Selection(
        string="Attendance Status", compute='_compute_attendance_state',
        selection=[('checked_out', "Checked out"), ('checked_in', "Checked in")],
        groups="hr_attendance.group_hr_attendance_kiosk,hr_attendance.group_hr_attendance,hr.group_hr_user")

    @api.depends('attendance_ids')
    def _compute_last_attendance_id(self):
        for employee in self:
            employee.last_attendance_id = self.env['hr.attendance'].search([
                ('employee_id', '=', employee.id),
            ], limit=1)

    @api.depends('last_attendance_id.check_in', 'last_attendance_id.check_out', 'last_attendance_id')
    def _compute_attendance_state(self):
        for employee in self:
            att = employee.last_attendance_id.sudo()
            # 檢查是否為異動日
            if att and att.check_in:
                check_in_date = (att.check_in + relativedelta(hours=+8)).date()
            now_date = (datetime.datetime.now() + relativedelta(hours=+8)).date()
            is_change_date = att and att.check_in and check_in_date != now_date
            if is_change_date:
                employee.attendance_state = 'checked_out'
            else:
                employee.attendance_state = att and not att.check_out and 'checked_in' or 'checked_out'
