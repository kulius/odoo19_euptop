# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import http, _
from odoo.http import request
from odoo.tools import float_round
import datetime
from datetime import timedelta


class StarryLordHrAttendance(http.Controller):

    @staticmethod
    def _get_employee_info_response(employee):
        response = {}
        if employee:
            # 查詢打卡紀錄
            check_date_time = (datetime.datetime.now() + timedelta(hours=8))
            attendance_check = employee.env['hr.attendance.check'].search(
                [('user_id', '=', employee.user_id.id), ('date', '=', check_date_time.date())], limit=1)
            response = {
                'id': employee.id,
                'employee_name': employee.name,
                'employee_avatar': employee.image_1920,
                'attendance_state': employee.attendance_state,
                'attendance': {'check_in_date': attendance_check.date,
                               'check_in': attendance_check.work_check_check_in_str,
                               'check_out': attendance_check.work_check_check_out_str},
                'display_systray': employee.company_id.attendance_from_systray,
                'display_overtime': employee.company_id.hr_attendance_display_overtime
            }
        return response

    @http.route('/sl_hr_attendance/attendance_user_data', type="json", auth="user")
    def user_attendance_data(self):
        employee = request.env.user.employee_id
        return self._get_employee_info_response(employee)
