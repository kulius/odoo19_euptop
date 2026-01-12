# -*- coding: utf-8 -*-
import datetime
from datetime import timedelta, time, date
import math
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError, UserError
from dateutil.relativedelta import relativedelta

from odoo.tools.safe_eval import pytz


class StarryLordAttendanceRepair(models.Model):
    _name = 'sl.attendance.repair'
    _description = '出勤異常說明單'

    name = fields.Char(string="主旨", required=True)

    end_date = fields.Datetime('下班時間')
    notes = fields.Text('事由說明')
    hour_from = fields.Selection(selection=[('0', '0'), ('1', '1'), ('2', '2'), ('3', '3'), ('4', '4'), ('5', '5'), ('6', '6'),
                                            ('7', '7'), ('8', '8'), ('9', '9'), ('10', '10'), ('11', '11'), ('12', '12'),
                                            ('13', '13'), ('14', '14'), ('15', '15'), ('16', '16'), ('17', '17'), ('18', '18'),
                                            ('19', '19'), ('20', '20'), ('21', '21'), ('22', '22'), ('23', '23')],
                                 string='上班打卡時間(小時)', )
    hour_to = fields.Selection(selection=[('0', '0'), ('1', '1'), ('2', '2'), ('3', '3'), ('4', '4'), ('5', '5'), ('6', '6'),
                                          ('7', '7'), ('8', '8'), ('9', '9'), ('10', '10'), ('11', '11'), ('12', '12'),
                                          ('13', '13'), ('14', '14'), ('15', '15'), ('16', '16'), ('17', '17'), ('18', '18'),
                                          ('19', '19'), ('20', '20'), ('21', '21'), ('22', '22'), ('23', '23')],
                               string='下班打卡時間(小時)', )
    min_from = fields.Selection(selection=[('0', '0'), ('1', '1'), ('2', '2'), ('3', '3'), ('4', '4'), ('5', '5'), ('6', '6'),
                                           ('7', '7'), ('8', '8'), ('9', '9'), ('10', '10'), ('11', '11'), ('12', '12'),
                                           ('13', '13'), ('14', '14'), ('15', '15'), ('16', '16'), ('17', '17'), ('18', '18'),
                                           ('19', '19'), ('20', '20'), ('21', '21'), ('22', '22'), ('23', '23'), ('24', '24')
        , ('25', '25'), ('26', '26'), ('27', '27'), ('28', '28'), ('29', '29'), ('30', '30')
        , ('31', '31'), ('32', '32'), ('33', '33'), ('34', '34'), ('35', '35'), ('36', '36')
        , ('37', '37'), ('38', '38'), ('39', '39'), ('40', '40'), ('41', '41'), ('42', '42')
        , ('38', '38'), ('39', '39'), ('40', '40'), ('41', '41'), ('42', '42')
        , ('43', '43'), ('44', '44'), ('45', '45'), ('46', '46'), ('47', '47'), ('48', '48')
        , ('49', '49'), ('50', '50'), ('51', '51'), ('52', '52'), ('53', '53'), ('54', '54')
        , ('55', '55'), ('56', '56'), ('57', '57'), ('58', '58'), ('59', '59')], default=None
                                , string='上班打卡時間(分鐘)', )
    min_to = fields.Selection(selection=[('0', '0'), ('1', '1'), ('2', '2'), ('3', '3'), ('4', '4'), ('5', '5'), ('6', '6'),
                                         ('7', '7'), ('8', '8'), ('9', '9'), ('10', '10'), ('11', '11'), ('12', '12'),
                                         ('13', '13'), ('14', '14'), ('15', '15'), ('16', '16'), ('17', '17'), ('18', '18'),
                                         ('19', '19'), ('20', '20'), ('21', '21'), ('22', '22'), ('23', '23'), ('24', '24')
        , ('25', '25'), ('26', '26'), ('27', '27'), ('28', '28'), ('29', '29'), ('30', '30')
        , ('31', '31'), ('32', '32'), ('33', '33'), ('34', '34'), ('35', '35'), ('36', '36')
        , ('37', '37'), ('38', '38'), ('39', '39'), ('40', '40'), ('41', '41'), ('42', '42')
        , ('38', '38'), ('39', '39'), ('40', '40'), ('41', '41'), ('42', '42')
        , ('43', '43'), ('44', '44'), ('45', '45'), ('46', '46'), ('47', '47'), ('48', '48')
        , ('49', '49'), ('50', '50'), ('51', '51'), ('52', '52'), ('53', '53'), ('54', '54')
        , ('55', '55'), ('56', '56'), ('57', '57'), ('58', '58'), ('59', '59')], default=None,
                              string='下班打卡時間(分鐘)', )

    department_id = fields.Many2one(
        comodel_name='hr.department',
        string="申請人部門",
        compute='_compute_department_id',
    )
    user_id = fields.Many2one(comodel_name='res.users', string="申請人", default=lambda self: self.env.user)
    employee_id = fields.Many2one(comodel_name='hr.employee.public', string="員工", default=lambda self: self.env.user.employee_id)
    sl_attendance_check_id = fields.Many2one(comodel_name='hr.attendance.check', string="出勤異常記錄", ondelete="set null",)
    start_date = fields.Date(string='異常打卡日期', related='sl_attendance_check_id.date', store=True)
    state = fields.Selection(selection=[('draft', '草稿'),
                                        ('f_approve', '待核准'),
                                        ('confirmed', '已同意'),
                                        ('refused', '不同意'),
                                        ('cancel', '取消')], string="狀態", default="draft")
    attendance_information = fields.Text(string='班表參考資訊', compute='compute_information', store='True')

    @api.depends('employee_id')
    def _compute_department_id(self):
        for rec in self:
            rec.department_id = rec.employee_id.department_id
            
    @api.onchange('employee_id')
    def _onchange_employee_id(self):
        for rec in self:
            rec.sl_attendance_check_id = False
            rec.name = ''

    @api.depends('sl_attendance_check_id', 'employee_id')
    def compute_information(self):
        for rec in self:
            # try:
            rec.attendance_information = ''
            fun = lambda x: x if x[0] != '0' else x[1:]

            attendance_ids = rec.env['hr.attendance'].search([('employee_id', '=', rec.employee_id.id),
                                                              ('check_in', '>=', rec.start_date),
                                                              ('check_out', '<=', rec.start_date)])
            for attendance_id in attendance_ids:
                rec.attendance_information += '考勤紀錄 '
                rec.attendance_information += fun(
                    datetime.datetime.strftime(attendance_id.check_in, '%Y-%m-%d %H:%M:%S') + ' - ')
                rec.attendance_information += fun(
                    datetime.datetime.strftime(attendance_id.check_out, '%Y-%m-%d %H:%M:%S'))
                rec.attendance_information += '\n'

            if not rec.employee_id.schedule_id.is_user_personal_calendar and rec.sl_attendance_check_id:
                start = rec.sl_attendance_check_id.date
                end = rec.sl_attendance_check_id.date
                current = start
                while current <= end:
                    worktime = self.env['hr.schedule.worktime'].sudo().search(
                        [('worktime_id', '=', self.employee_id.schedule_id.id),
                         ('date_type', '=', 'schedule'),
                         ('dayofweek', '=', current.weekday()),
                         ])
                    if worktime:
                        rec.attendance_information += '班表 '
                        rec.attendance_information += '%s 上午 %s~%s ' % (
                            current.strftime('%Y-%m-%d'), worktime.am_start, worktime.am_end)
                        rec.attendance_information += '~ 下午 %s~%s' % (worktime.pm_start, worktime.pm_end)
                        rec.attendance_information += '\n'

                    current += timedelta(days=1)
                rec.attendance_information += rec.sl_attendance_check_id.work_memo

            # except:
            #     return False

    @api.constrains('hour_from', 'min_from', 'hour_to', 'min_to')
    def _check_time_fields(self):
        for rec in self:
            # 開始時間、結束時間必須成對出現
            if (rec.hour_from and not rec.min_from) or (rec.min_from and not rec.hour_from):
                raise ValidationError('請選擇完整的「開始時間（時、分）」')
            if (rec.hour_to and not rec.min_to) or (rec.min_to and not rec.hour_to):
                raise ValidationError('請選擇完整的「結束時間（時、分）」')
            # 至少要有一組
            if not ((rec.hour_from and rec.min_from) or (rec.hour_to and rec.min_to)):
                raise ValidationError('請填寫完整的開始或結束時間（時、分）')

    @api.onchange('sl_attendance_check_id')
    def onchange_start_date(self):
        self.name = " %s %s 出勤異常說明單" % (self.employee_id.name, self.start_date)

    def to_draft(self):
        for rec in self:
            rec.state = 'draft'

    def to_refused(self):
        for rec in self:
            rec.state = 'refused'

    def to_cancel(self):
        for rec in self:
            rec.state = 'cancel'

    def to_f_approve(self):
        for rec in self:
            rec.state = 'f_approve'

    def agree(self):
        """批准補卡申請"""
        for rec in self:
            rec.state = 'confirmed'
            # current_date = fields.Date.from_string(rec.start_date)
            # 获取用户的时区
            # user_tz = self.env.user.tz or 'UTC'
            # local_tz = pytz.timezone(user_tz)

            # 當地時間一天的開始跟結束
            # start_datetime_local = datetime.datetime.combine(current_date, time.min)
            # end_datetime_local = datetime.datetime.combine(current_date, time.max)

            # 转换为UTC
            # start_datetime_utc = local_tz.localize(start_datetime_local).astimezone(pytz.utc)
            # end_datetime_utc = local_tz.localize(end_datetime_local).astimezone(pytz.utc)

            # 格式化为字符串，因为搜索可能需要字符串格式
            # start_datetime_utc_str = start_datetime_utc.strftime('%Y-%m-%d %H:%M:%S')
            # end_datetime_utc_str = end_datetime_utc.strftime('%Y-%m-%d %H:%M:%S')

            # start_datetime = datetime.datetime.combine(rec.start_date, time(hour=0, minute=0, second=0))
            # end_datetime = start_datetime + timedelta(days=1)
            # # 將當日打卡資料停用
            # attendance_rec = self.env['hr.attendance'].search([('employee_id', '=', rec.employee_id.id),
            #                                                    ('check_in', '>=', start_datetime_utc_str),
            #                                                    ('check_in', '<=', end_datetime_utc_str)])
            #
            # attendance_rec.write({'active': False})
            # new_check_in = datetime.datetime.combine(rec.start_date,
            #                                          time(hour=int(rec.hour_from), minute=int(rec.min_from)))
            # new_check_out = datetime.datetime.combine(rec.start_date,
            #                                           time(hour=int(rec.hour_to), minute=int(rec.min_to)))
            # # 轉換成UTC
            # check_in_utc = local_tz.localize(new_check_in).astimezone(pytz.utc).replace(tzinfo=None)
            # check_out_utc = local_tz.localize(new_check_out).astimezone(pytz.utc).replace(tzinfo=None)
            # self.env['hr.attendance'].create({
            #     'employee_id': rec.employee_id.id,
            #     'check_in': check_in_utc,
            #     'check_out': check_out_utc,
            # })


