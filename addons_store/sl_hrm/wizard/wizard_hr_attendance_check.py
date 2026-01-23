from dateutil.relativedelta import relativedelta

from odoo import models, api, fields


class WizardHrAttendanceCheck(models.TransientModel):
    _name = 'wizard.hr.attendance.check'
    _description = '出勤紀錄精靈'
    # 預設值為本月第ㄧ天
    start_day = fields.Date(string='開始日期', required=True,
                            default=lambda self: fields.Date.from_string(fields.Date.today()).replace(day=1))

    # 預設為本月最後一天
    end_day = fields.Date(string='結束日期', required=True,
                          default=lambda self: fields.Date.from_string(fields.Date.today()).replace(
                              day=1) + relativedelta(months=1, day=1, days=-1))

    def delete(self):
        records = self.env['hr.attendance.check'].search([
            ('date', '>=', self.start_day),
            ('date', '<=', self.end_day)
        ])
        if records:
            records.unlink()

    def add(self):
        # 取得action
        # 取得今天的日期
        # today = fields.Date.from_string()

        # # 利用今天()計算出本月第一天的日期
        # first_day = fields.Date.from_string(fields.Date.today()).replace(day=1)
        # # 利用today()計算出本月最後一天的日期
        # last_day = fields.Date.from_string(fields.Date.today()).replace(day=1) + relativedelta(months=1, day=1, days=-1)

        employee_ids = self.env['hr.employee'].search([('state', '=', 'working'), ('is_no_need_check_in', '=', False)]).ids

        self.env['hr.attendance.check'].create_attendance_records(self.start_day, self.end_day, employee_ids)

        action = self.env.ref('sl_hrm.hr_attendance_check_manager_action').sudo().read()[0]
        action['context'] = {
            # 'search_default_date': "[('date', '>=', context.get('start_date'))]",
            'start_date': self.start_day,
            'end_date': self.end_day,
            'search_default_filter_start_and_end': True
        }

        return action
