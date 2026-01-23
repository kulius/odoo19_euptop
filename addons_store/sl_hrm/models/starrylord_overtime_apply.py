import math
import calendar
from datetime import timedelta, time, date, datetime
from odoo import api, fields, models, exceptions, _
from odoo.exceptions import UserError
from dateutil.relativedelta import relativedelta


class StarryLordOvertimeApply(models.Model):
    _name = 'starrylord.overtime.apply'
    _description = '加班申請'
    _inherit = 'mail.thread'
    _order = 'create_date desc, id desc'

    name = fields.Char(string='單號')
    employee_id = fields.Many2one('hr.employee.public', string='申請人',
                                  default=lambda self: self.env.user.employee_id.id,
                                  required=True)
    user_id = fields.Many2one('res.users', string='User', related='employee_id.user_id', related_sudo=True,
                              compute_sudo=True, store=True, readonly=True)
    company_id = fields.Many2one(comodel_name="res.company", string="公司別", related="employee_id.company_id", )
    department_id = fields.Many2one('hr.department', string="部門",
                                    related="employee_id.department_id")
    department_name = fields.Char(
        string='部門名稱',
        related="employee_id.department_id.name",
        store=True
    )

    employee_info = fields.Char(
        string='員工資訊',
        compute='_compute_employee_info',
        store=True
    )
    start_day_format = fields.Char(string='使用日期（格式化）', compute='_compute_start_day_str', store=True)

    job_id = fields.Many2one('hr.job', string="職稱", related="employee_id.job_id", store=True, related_sudo=True)
    manager_id = fields.Many2one('res.users', string="管理人",
                                 related="employee_id.parent_id.user_id", store=True)

    start_day = fields.Date(string='加班日期', required=True)

    hour_from = fields.Selection([('0', '0'), ('1', '1'), ('2', '2'), ('3', '3'), ('4', '4'), ('5', '5'), ('6', '6'),
                                  ('7', '7'), ('8', '8'), ('9', '9'), ('10', '10'), ('11', '11'), ('12', '12'),
                                  ('13', '13'), ('14', '14'), ('15', '15'), ('16', '16'), ('17', '17'), ('18', '18'),
                                  ('19', '19'), ('20', '20'), ('21', '21'), ('22', '22'), ('23', '23')], string='開始時間'
                                 , required=True)
    hour_to = fields.Selection([('0', '0'), ('1', '1'), ('2', '2'), ('3', '3'), ('4', '4'), ('5', '5'), ('6', '6'),
                                ('7', '7'), ('8', '8'), ('9', '9'), ('10', '10'), ('11', '11'), ('12', '12'),
                                ('13', '13'), ('14', '14'), ('15', '15'), ('16', '16'), ('17', '17'), ('18', '18'),
                                ('19', '19'), ('20', '20'), ('21', '21'), ('22', '22'), ('23', '23'), ('24', '24')],
                               string='結束時間',
                               required=True)
    min_from = fields.Selection([('0', '00'), ('0.25', '15'), ('0.5', '30'), ('0.75', '45')],
                                string='開始時間')
    min_to = fields.Selection([('0', '00'), ('0.25', '15'), ('0.5', '30'), ('0.75', '45')],
                              string='結束時間')
    apply_from = fields.Datetime(string='加班開始時間', store=True)
    apply_to = fields.Datetime(string='加班結束時間', store=True)

    time_type = fields.Selection([("hour", "小時"), ("half", "半小時"), ("quarter", "十五分鐘")],
                                 related="overtime_type_id.time_type", related_sudo=True, compute_sudo=True, store=True)
    duration_time = fields.Float(string='時長(小時)', required=True)
    type = fields.Selection([('cash', '加班費'), ('holiday', '補休')], default="holiday", string="選擇", required=True,)
    has_overtime_meal_allowance = fields.Boolean(string='是否有誤餐費')
    without_rest_time = fields.Boolean(string='中午無休息連續工作?')
    overtime_type_id = fields.Many2one('starrylord.overtime.type', string="加班類型", required=True)
    attached = fields.Many2many('ir.attachment', string='附件')
    desc = fields.Char(string='加班事由')
    state = fields.Selection([('draft', '草稿'),
                              ('f_approve', '待核准'),
                              ('agree', '核准加班'),
                              ('refused', '己拒絕')], string="狀態",
                             default="draft", traceback=True)
    sl_holiday_allocation_ids = fields.One2many('starrylord.holiday.allocation', string='休假分配', inverse_name='sl_overtime_apply_id')
    hr_personal_calendar_id = fields.Many2one('hr.personal.calendar', string='行事曆')

    allocation_validity_end = fields.Date(
        string='補休截止日期',
        compute='_compute_allocation_validity_end',
        store=True,
        help='選定的補休分配之使用截止日期，可由審核人員調整'
    )

    hr_confirm_state = fields.Selection(
        [
            ('pending', '單據待確認'),
            ('confirmed', '單據已生效'),
            ('invalid', '單據未符合'),
        ],
        string='人資確認狀態',
        default='pending',
        tracking=True
    )

    sl_holiday_allocation_ids = fields.One2many(
        'starrylord.holiday.allocation',
        'sl_overtime_apply_id',
        string='補休分配'
    )

    holiday_allocation_count = fields.Integer(
        string='補休筆數',
        compute='_compute_holiday_allocation_count'
    )

    # 20260111 合規判斷
    compliance_state = fields.Selection(
        [
            ('pending', '待確認合規'),
            ('ok', '合規'),
            ('ng', '不合規'),
        ],
        string='合規判斷',
        default='pending',
        tracking=True
    )

    compliance_reason = fields.Text(
        string='不合規原因'
    )

    # 20260111

    # === 出勤勾稽 ===
    attendance_ids = fields.Many2many(
        'hr.attendance',
        string='出勤紀錄',
        copy=False
    )

    attendance_check_ids = fields.Many2many(
        'hr.attendance.check',
        string='出勤檢查',
        copy=False
    )

    attendance_check_result = fields.Selection(
        [
            ('ok', '出勤無異常'),
            ('ng', '出勤異常'),
        ],
        string='資料檢查結果',
        tracking=True
    )

    overtime_attendance_process_state = fields.Selection(
        [
            ('pending', '出勤檢核待處理'),
            ('done', '已處理'),
            ('no_issue', '無異常'),
        ],
        string='加班異常處理進度',
        default='pending',
        tracking=True
    )

    # === 調整後時間（人工調整用，後續 Wizard 會寫）===
    adjust_hour_from = fields.Selection(
        selection=lambda self: self._get_hour_selection(),
        string='調整後開始小時'
    )
    adjust_min_from = fields.Selection(
        selection=[('0', '00'), ('0.25', '15'), ('0.5', '30'), ('0.75', '45')],
        string='調整後開始分鐘'
    )
    adjust_hour_to = fields.Selection(
        selection=lambda self: self._get_hour_selection(end=True),
        string='調整後結束小時'
    )
    adjust_min_to = fields.Selection(
        selection=[('0', '00'), ('0.25', '15'), ('0.5', '30'), ('0.75', '45')],
        string='調整後結束分鐘'
    )

    adjust_duration_time = fields.Float(
        string='調整後加班時長',
        help='若有異常並人工調整，後續薪資 / 補休皆以此欄位為準'
    )

    overtime_adjust_memo = fields.Char(
        string='加班調整紀錄',
        tracking=True
    )

    hr_invalid_reason = fields.Text(
        string='人資未符合原因',
        tracking=True
    )

    attendance_abnormal_reason = fields.Text(
        string='加班考勤異常原因',
        tracking=True,
        help='系統於考勤檢查時自動產生的異常說明'
    )

    # 加班異常時間調整功能
    def action_open_overtime_adjust_wizard(self):
        self.ensure_one()

        if self.attendance_check_result != 'ng':
            raise UserError('此加班單無考勤異常，無需進行異常處理')

        if self.overtime_attendance_process_state != 'pending':
            raise UserError('此加班單已完成異常處理')

        return {
            'type': 'ir.actions.act_window',
            'name': '加班異常處理',
            'res_model': 'starrylord.overtime.attendance.adjust.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_overtime_apply_id': self.id,
            }
        }


    # 共用 hour selection
    def _get_hour_selection(self, end=False):
        end_hour = 24 if end else 23
        return [(str(i), str(i)) for i in range(0, end_hour + 1)]

    def action_check_attendance(self):
        """
        檢查加班單是否有『單筆』出勤紀錄完整涵蓋
        容忍規則：允許加班開始「晚進」、結束「早退」各 ±5 分鐘
        """
        TOLERANCE_MINUTES = 5

        for rec in self:
            if not rec.apply_from or not rec.apply_to:
                continue

            employee = rec.employee_id
            apply_from = rec.apply_from
            apply_to = rec.apply_to

            # === 正確的容忍定義（放寬，不是加嚴）===
            tolerant_start = apply_from + timedelta(minutes=TOLERANCE_MINUTES)
            tolerant_end = apply_to - timedelta(minutes=TOLERANCE_MINUTES)

            # === 搜尋用範圍（只用來撈資料）===
            search_from = apply_from - timedelta(minutes=TOLERANCE_MINUTES)
            search_to = apply_to + timedelta(minutes=TOLERANCE_MINUTES)

            # === 1. 抓 hr.attendance ===
            attendances = self.env['hr.attendance'].search([
                ('employee_id', '=', employee.id),
                ('check_in', '<=', search_to),
                ('check_out', '>=', search_from),
            ])

            # === 2. 抓 hr.attendance.check（留稽核）===
            attendance_checks = self.env['hr.attendance.check'].search([
                ('employee_id', '=', employee.id),
                ('date', '>=', apply_from.date()),
                ('date', '<=', apply_to.date()),
            ])

            # === 3. 寫入稽核關聯 ===
            rec.attendance_ids = [(6, 0, attendances.ids)]
            rec.attendance_check_ids = [(6, 0, attendance_checks.ids)]

            for check in attendance_checks:
                check.write({
                    'overtime_apply_ids': [(4, rec.id)]
                })

            # === 4. 核心判斷 ===
            matched_attendance = False
            has_attendance = False
            only_full_day_attendance = True

            for att in attendances:
                if not att.check_in or not att.check_out:
                    continue

                has_attendance = True

                # 排除整天打卡（例如 09:00~21:00）
                if att.check_in < search_from and att.check_out > search_to:
                    continue
                else:
                    only_full_day_attendance = False

                # 正確的涵蓋判斷（容忍後）
                if att.check_in <= tolerant_start and att.check_out >= tolerant_end:
                    matched_attendance = True
                    break

            # === 5. 寫回結果 ===
            if matched_attendance:
                rec.attendance_check_result = 'ok'
                rec.overtime_attendance_process_state = 'no_issue'
                rec.attendance_abnormal_reason = False

                # 預設調整欄位 = 原始加班
                rec.adjust_hour_from = rec.hour_from
                rec.adjust_min_from = rec.min_from
                rec.adjust_hour_to = rec.hour_to
                rec.adjust_min_to = rec.min_to
                rec.adjust_duration_time = rec.duration_time

                # === 自動 HR 確認（嚴格條件）===
                if (
                    rec.state == 'agree'
                    and rec.hr_confirm_state == 'pending'
                    and rec.adjust_duration_time == rec.duration_time
                ):
                    rec.action_hr_confirm()

            else:
                rec.attendance_check_result = 'ng'
                rec.overtime_attendance_process_state = 'pending'

                # === 組合異常原因 ===
                abnormal_reasons = []

                if not has_attendance:
                    abnormal_reasons.append('查無任何打卡紀錄')
                elif only_full_day_attendance:
                    abnormal_reasons.append('僅有整天打卡紀錄，未能作為加班依據')
                else:
                    abnormal_reasons.append('打卡時間未涵蓋加班申請時段（已套用容忍時間）')

                # 加班申請
                abnormal_reasons.append(
                    f'【加班申請】{rec.start_day} '
                    f'{rec.hour_from}:{int(float(rec.min_from) * 60):02d} ~ '
                    f'{rec.hour_to}:{int(float(rec.min_to) * 60):02d}'
                )

                # 實際打卡
                if attendances:
                    lines = []
                    for att in attendances:
                        if not att.check_in or not att.check_out:
                            continue
                        check_in = (att.check_in + timedelta(hours=8)).strftime('%Y-%m-%d %H:%M')
                        check_out = (att.check_out + timedelta(hours=8)).strftime('%Y-%m-%d %H:%M')
                        lines.append(f'{check_in} ~ {check_out}')

                    abnormal_reasons.append('【實際打卡】' + '；'.join(lines))
                else:
                    abnormal_reasons.append('【實際打卡】無')

                rec.attendance_abnormal_reason = '；'.join(abnormal_reasons)

    # 人資合規判斷
    def action_open_compliance_wizard(self):
        self.ensure_one()

        return {
            'type': 'ir.actions.act_window',
            'name': '合規判斷',
            'res_model': 'starrylord.overtime.compliance.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_overtime_apply_id': self.id,
            }
        }


    # 智慧按鈕 可以查看補休
    def action_view_holiday_allocations(self):
        self.ensure_one()

        return {
            'type': 'ir.actions.act_window',
            'name': '補休分配',
            'res_model': 'starrylord.holiday.allocation',
            'view_mode': 'list,form',
            'domain': [('sl_overtime_apply_id', '=', self.id)],
            'context': {
                'default_sl_overtime_apply_id': self.id,
                'default_employee_id': self.employee_id.id,
            }
        }

    @api.depends('sl_holiday_allocation_ids')
    def _compute_holiday_allocation_count(self):
        for rec in self:
            rec.holiday_allocation_count = len(rec.sl_holiday_allocation_ids)


    @api.depends('start_day', 'type')
    def _compute_allocation_validity_end(self):
        for rec in self:
            if rec.type == 'cash':
                rec.allocation_validity_end = rec.start_day
            elif rec.start_day:
                rec.allocation_validity_end = (rec.start_day + relativedelta(months=6, day=1)) - relativedelta(days=1)
            else:
                rec.allocation_validity_end = False

    @api.depends('employee_id')
    def _compute_employee_info(self):
        for rec in self:
            rec.employee_info = f"{rec.department_name}\\{rec.employee_id.employee_number}\\{rec.employee_id.name}"

    @api.depends('start_day')
    def _compute_start_day_str(self):
        for rec in self:
            if rec.start_day:
                rec.start_day_format = rec.start_day.strftime('%Y-%m-%d')  # 或 '%Y-%-m-%-d' for Linux
            else:
                rec.start_day_format = ''

    @api.onchange('start_day')
    def start_day_onchange(self):
        if self.start_day:
            start = datetime.combine(self.start_day, time(hour=0, minute=0, second=0))
            # start += relativedelta(hours=-8)
            end = datetime.combine(self.start_day, time(hour=23, minute=59, second=59))
            # end += relativedelta(hours=-8)
            date_type = self.env['hr.personal.calendar'].search([('start_date', '>=', start), ('end_date', '<=', end),
                                                                 ('employee_id', '=', self.employee_id.id),
                                                                 ('date_type', '!=', 'leave'),
                                                                 ('date_type', '!=', 'overtime'),
                                                                 ('date_type', '!=', 'no_work')],
                                                                order="create_date asc", limit=1).date_type
            if date_type:
                self.overtime_type_id = self.env['starrylord.overtime.type'].search([('date_type', '=', date_type)],
                                                                                    order="create_date asc", limit=1)

    def unlink(self):
        for rec in self:
            if rec.state != 'draft':
                raise UserError(
                    _("您不能刪除送出的加班單")
                )
        return super(StarryLordOvertimeApply, self).unlink()

    def copy(self, default=None):
        for rec in self:
            if rec.state != 'draft':
                raise UserError(
                    _("您不能複製送出的加班單")
                )
        return super().copy(default)

    # 將float型態的時間轉為time後合併
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
        datetime_obj = datetime.combine(date_field, time_obj)
        # 時區校正
        datetime_obj -= timedelta(hours=8)

        return datetime_obj

    @api.model
    def create(self, vals):
        vals['name'] = self.env['ir.sequence'].next_by_code('starrylord.overtime.number')
        res = super(StarryLordOvertimeApply, self).create(vals)
        regular_holiday_exclude_payroll = self.env['ir.config_parameter'].sudo().get_param('sl_hrm_payroll.regular_holiday_exclude_payroll', default=False)
        if regular_holiday_exclude_payroll and self.overtime_type_id.date_type == 'regular_holiday':
            res.write({'type': 'cash'})
        return res

    @api.model
    def write(self, vals):
        # 如果是例假日加班, 直接設定現金
        regular_holiday_exclude_payroll = self.env['ir.config_parameter'].sudo().get_param('sl_hrm_payroll.regular_holiday_exclude_payroll', default=False)
        if regular_holiday_exclude_payroll and self.overtime_type_id.date_type == 'regular_holiday':
            vals['type'] = 'cash'
        res = super(StarryLordOvertimeApply, self).write(vals)
        return res

    @api.onchange('duration_time')
    def check_overtime(self):
        for rec in self:
            all_time = 0
            all_time_three = 0
            setting = self.env['ir.config_parameter'].sudo()
            max_overtime_month = int(setting.get_param('max_overtime_month', default=False))  # 單月加班時數上限
            max_overtime_three_month = int(setting.get_param('max_overtime_three_month', default=False))  # 三月內加班時數上限
            all_overtime = rec.env['starrylord.overtime.apply'].search([('employee_id', '=', rec.employee_id.id)])
            try:
                first_day = rec.start_day + relativedelta(day=1)
                last_day = rec.start_day + relativedelta(day=1, month=rec.start_day.month + 1)
                last_day -= timedelta(days=1)
                one_month = all_overtime.filtered(lambda x: last_day >= x.start_day >= first_day)
                for one in one_month:
                    all_time += one.duration_time
                if not rec.id:
                    all_time += rec.duration_time
                # first_day -= relativedelta(month=2)
                # 依照四季計算加班時數上限
                if rec.start_day.month <= 3:
                    season = 1
                elif rec.start_day.month <= 6:
                    season = 2
                elif rec.start_day.month <= 9:
                    season = 3
                else:
                    season = 4
                # 取得每一季的第一天
                if season == 1:
                    season_first_day = first_day + relativedelta(day=1, month=1)
                    season_last_day = first_day + relativedelta(day=1, month=4)
                    season_last_day -= timedelta(days=1)
                elif season == 2:
                    season_first_day = first_day + relativedelta(day=1, month=4)
                    season_last_day = first_day + relativedelta(day=1, month=7)
                    season_last_day -= timedelta(days=1)
                elif season == 3:
                    season_first_day = first_day + relativedelta(day=1, month=7)
                    season_last_day = first_day + relativedelta(day=1, month=10)
                    season_last_day -= timedelta(days=1)
                else:
                    season_first_day = first_day + relativedelta(day=1, month=10)
                    season_last_day = first_day + relativedelta(day=31, month=12)
                # print(season_first_day, season_last_day)

                three_month = all_overtime.filtered(lambda x: season_last_day >= x.start_day >= season_first_day)
                for three in three_month:
                    all_time_three += three.duration_time
                if not rec.id:
                    all_time_three += rec.duration_time
            except:
                return
            if all_time > max_overtime_month != 0:
                return {
                    'warning': {
                        'title': 'Warning!',
                        'message': '超過單月加班時數上限(%s小時) 本月已加班時數%s' % ( max_overtime_month,all_time)}
                }
                # raise UserError('超過單月加班時數上限(%s小時) 本月已加班時數%s' % ( max_overtime_month,all_time))
            elif all_time_three > max_overtime_three_month != 0:
                return {
                    'warning': {
                        'title': 'Warning!',
                        'message': '超過第%s季三個月月加班時數上限(%s小時) 本季已加班時數%s' % (season, max_overtime_three_month, all_time_three)}
                }
                # raise UserError('超過第%s季三個月月加班時數上限(%s小時) 本季已加班時數%s' % (season, max_overtime_three_month, all_time_three))

    def merge_time_field(self, day, hour, minute):
        if day and hour and minute:
            hours = int(hour)
            minutes = int(float(minute) * 60)  # Convert 0.5 to 30 minutes
            # Combine the date and time into a datetime
            s_datetime = datetime.combine(
                fields.Date.from_string(day),  # Convert the string date to a date object
                time(hour=hours, minute=minutes)
            )
        else:
            s_datetime = False
        return s_datetime

    @api.onchange('start_day')
    def get_overtime_type(self):  # 根據班表判斷加班類型
        if not self.start_day:
            return False
        # 判斷星期一至星期五是平日加班, 星期六是休假日加班, 星期日是例假日加班, 是否為國定假日
        public_holiday = self.env['hr.public.holiday'].search([('start_date', '>=', self.merge_date_time(self.start_day, 0)),
                                                               ('start_date', '<=', self.merge_date_time(self.start_day, 23.983333333333334))])
        if public_holiday and public_holiday.holiday_type == 'holiday':  # 國定假日
            self.overtime_type_id = self.env['starrylord.overtime.type'].search([('date_type', '=', 'holiday')],
                                                                                order="create_date asc", limit=1)
        elif public_holiday and public_holiday.holiday_type == 'make_up_day':  # 補班日
            self.overtime_type_id = self.env['starrylord.overtime.type'].search([('date_type', '=', 'schedule')],
                                                                                order="create_date asc", limit=1)
        elif 0 <= self.start_day.weekday() < 5:
            self.overtime_type_id = self.env['starrylord.overtime.type'].search([('date_type', '=', 'schedule')],
                                                                                order="create_date asc", limit=1)
        elif self.start_day.weekday() == 5:
            self.overtime_type_id = self.env['starrylord.overtime.type'].search([('date_type', '=', 'day_off')],
                                                                                order="create_date asc", limit=1)
        elif self.start_day.weekday() == 6:
            self.overtime_type_id = self.env['starrylord.overtime.type'].search([('date_type', '=', 'regular_holiday')],
                                                                                order="create_date asc", limit=1)

    def convert_float_time_to_string(self, time_float):
        if time_float is None:
            return None
        hours = int(time_float)
        minutes = int((time_float - hours) * 60)
        return f"{hours:02d}:{minutes:02d}"

    @api.onchange('start_day', 'hour_from', 'min_from', 'hour_to', 'min_to', 'without_rest_time', 'has_overtime_meal_allowance')
    def calc_duration_time(self):
        if not (self.start_day and self.hour_from and self.min_from and self.hour_to and self.min_to):
            return False
        apply_from = False
        apply_to = False
        if self.start_day and self.hour_from and self.min_from:
            apply_from = self.merge_time_field(self.start_day, self.hour_from, self.min_from)
            self.apply_from = apply_from + relativedelta(hours=-8)  # 轉換成UTC

        if self.start_day and self.hour_to and self.min_to:
            if self.hour_to == '24':
                end_day = self.start_day + relativedelta(days=1)
                hour = '0'
            else:
                end_day = self.start_day
                hour = self.hour_to
            apply_to = self.merge_time_field(end_day, hour, self.min_to)
            self.apply_to = apply_to + relativedelta(hours=-8)  # 轉換成UTC

        if not self.employee_id.schedule_id:
            raise UserError('未設定員工班表')

        if apply_from > apply_to:
            raise UserError('開始時間，不可大於結束時間')

        if self.check_duty_over_6days():
            self.start_day = None
            return {
                'warning': {
                    'title': '超時警告',
                    'message': str('已連續 7 天上班，違反勞基法！')
                }
            }

        if apply_from and apply_to:
            if self.employee_id.schedule_id.is_user_personal_calendar:  # 使用個人班表
                # 查詢出hr.personal.calendar當天的班表
                schedule_list = self.env['hr.personal.calendar'].search([('employee_id', '=', self.employee_id.id)])

                # 找到當天的班表
                schedule_ids = schedule_list.filtered(
                    lambda x: (x.start_date + relativedelta(hours=+8)).date() >= self.start_day >= (
                            x.end_date + relativedelta(hours=+8)).date())

                total_overtime_hours = 0

                for schedule in schedule_ids:
                    work_start = schedule.start_date + relativedelta(hours=+8)  # 上班開始時間
                    work_end = schedule.end_date + relativedelta(hours=+8.5)   # 下班結束時間（含休息0.5小時）

                    # 計算提早上班的時數（在上班時間前的加班）
                    if apply_from < work_start:
                        early_overtime_end = min(apply_to, work_start)
                        if early_overtime_end > apply_from:
                            early_overtime_hours = (early_overtime_end - apply_from).total_seconds() / 3600
                            total_overtime_hours += early_overtime_hours

                    # 計算下班後的加班時數
                    if apply_to > work_end:
                        late_overtime_start = max(apply_from, work_end)
                        if apply_to > late_overtime_start:
                            late_overtime_hours = (apply_to - late_overtime_start).total_seconds() / 3600
                            total_overtime_hours += late_overtime_hours

                self.duration_time = total_overtime_hours
            else:  # 使用每日8hr班表
                public_holiday = self.env['hr.public.holiday'].search([('start_date', '>=', self.merge_date_time(self.start_day, 0)),
                                                                       ('start_date', '<=', self.merge_date_time(self.start_day, 23.983333333333334))])
                if public_holiday and public_holiday.holiday_type in ['holiday', 'regular_holiday']:  # 國定假日,例假日
                    # 國定假日/例假日 做1給8
                    overtime_duration_time = (apply_to - apply_from).total_seconds() / 3600
                    overtime_duration_time = 8 if overtime_duration_time <= 8 else overtime_duration_time - 1
                    if self.without_rest_time:
                        overtime_duration_time += 1
                    self.duration_time = overtime_duration_time
                elif public_holiday and public_holiday.holiday_type in ['day_off']:  # 休息日
                    overtime_duration_time = (apply_to - apply_from).total_seconds() / 3600
                    overtime_duration_time = overtime_duration_time - 1 if overtime_duration_time >= 5 else overtime_duration_time
                    if self.without_rest_time:
                        overtime_duration_time += 1
                    if self.has_overtime_meal_allowance:
                        overtime_duration_time -= 0.5
                    self.duration_time = overtime_duration_time


                else:
                    # 平日加班的處理
                    total_overtime_hours = 0

                    if public_holiday and public_holiday.holiday_type == 'make_up_day':  # 補班日
                        worktime_list = self.env['hr.schedule.worktime'].sudo().search(
                            [('worktime_id', '=', self.employee_id.schedule_id.id),
                             ('date_type', 'in', ['schedule']),
                             ('dayofweek', '=', apply_from.weekday() - 1),
                             ])
                    else:
                        worktime_list = self.env['hr.schedule.worktime'].sudo().search(
                            [('worktime_id', '=', self.employee_id.schedule_id.id),
                             ('date_type', 'in', ['schedule']),
                             ('dayofweek', '=', apply_from.weekday()),
                             ])

                    if worktime_list:
                        for worktime in worktime_list:
                            # 計算工作開始時間
                            if worktime.work_start:
                                work_start_hour = math.floor(worktime.work_start)
                                work_start_min = round((worktime.work_start % 1) * 60)
                                if work_start_min == 60:
                                    work_start_min = 0
                                    work_start_hour = work_start_hour + 1
                                work_start_datetime = apply_from.replace(hour=work_start_hour, minute=work_start_min)

                                # 計算提早上班的加班時數（在工作開始時間前）
                                if apply_from < work_start_datetime:
                                    early_overtime_end = min(apply_to, work_start_datetime)
                                    if early_overtime_end > apply_from:
                                        early_overtime_hours = (early_overtime_end - apply_from).total_seconds() / 3600
                                        total_overtime_hours += early_overtime_hours

                            # 計算工作結束時間後的加班
                            if worktime.work_end:  # 有設定結束時間
                                worktime_hour_part = math.floor(worktime.work_end)
                                worktime_min_part = round((worktime.work_end % 1) * 60)
                                if worktime_min_part == 60:
                                    worktime_min_part = 0
                                    worktime_hour_part = worktime_hour_part + 1
                                work_end_datetime = apply_from.replace(hour=worktime_hour_part, minute=worktime_min_part)

                                # 計算下班後的加班時數
                                if apply_to > work_end_datetime:
                                    late_overtime_start = max(apply_from, work_end_datetime)
                                    if apply_to > late_overtime_start:
                                        late_overtime_hours = (apply_to - late_overtime_start).total_seconds() / 3600
                                        total_overtime_hours += late_overtime_hours
                    else:
                        # 如果沒有找到班表，就直接計算總時數
                        total_overtime_hours = (apply_to - apply_from).total_seconds() / 3600

                    self.duration_time = total_overtime_hours
        else:
            self.duration_time = 0

        # 計算完時數後，進行勞基法驗證
        if self.duration_time > 0 and self.overtime_type_id:
            try:
                self.check_labor_law_overtime_limit(self)
            except UserError as e:
                # 在 onchange 中顯示警告而不是錯誤
                return {
                    'warning': {
                        'title': '勞基法規定警告',
                        'message': str(e)
                    }
                }
    def check_overtime_time_min_unit(self, rec):
        # 檢查加班時數是否符合系統設定的最小單位
        setting = self.env['ir.config_parameter'].sudo()
        min_overtime_unit = setting.get_param('min_overtime_unit', default='half')

        if min_overtime_unit:
            if min_overtime_unit == 'hour':
                if rec.duration_time % 1 != 0:
                    raise UserError('加班時數必須以小時為單位')
            elif min_overtime_unit == 'half':
                if rec.duration_time % 0.5 != 0:
                    raise UserError('加班時數必須以半小時為單位')
            elif min_overtime_unit == 'quarter':
                if rec.duration_time % 0.25 != 0:
                    raise UserError('加班時數必須以十五分鐘為單位')

        # 依照勞基法規定檢查單次加班時數上限
        self.check_labor_law_overtime_limit(rec)

    def check_labor_law_overtime_limit(self, rec):
        """
        依照勞基法規定檢查單次加班時數上限
        - 平日加班：最多4小時
        - 假日加班：最多12小時
        """
        if not rec.overtime_type_id:
            return

        # 判斷是否為平日或假日
        self.get_overtime_type()
        date_type = rec.overtime_type_id.date_type

        if date_type == 'schedule':  # 平日加班
            if rec.duration_time > 4:
                raise UserError('依勞基法規定，平日加班時數不得超過4小時\n您申請了%.2f小時，請調整加班時數' % rec.duration_time)
        elif date_type in ['day_off', 'regular_holiday', 'holiday']:  # 假日加班（休假日、例假日、國定假日）
            if rec.duration_time > 12:
                raise UserError('依勞基法規定，假日加班時數不得超過12小時\n您申請了%.2f小時，請調整加班時數' % rec.duration_time)

    def check_duty_over_6days(self):
        employee_id = self.employee_id
        apply_date = self.start_day

        start_date = apply_date - timedelta(days=6)
        end_date = apply_date + timedelta(days=6)

        calendar = employee_id.schedule_id
        if not calendar:
            schedule_weekdays = []
        else:
            schedule_weekdays = [int(att.dayofweek) for att in calendar.worktime_ids if att.date_type == 'schedule']

        # 2. 撈全日請假
        leaves = self.env['starrylord.holiday.apply'].search([
            ('employee_id', '=', employee_id.id),
            ('state', '!=', 'draft'),
            ('start_day', '>=', start_date),
            ('end_day', '<=', end_date),
        ])

        overtimes = self.env['starrylord.overtime.apply'].search([
            ('employee_id', '=', employee_id.id),
            ('state', '!=', 'draft'),
            ('start_day', '>=', start_date),
            ('start_day', '<=', end_date),
        ])

        current_date = start_date
        streak = 0
        over = False
        while current_date <= end_date:
            if current_date == apply_date:
                is_working = True
            # 有加班 → True
            elif any(ot.start_day == current_date for ot in overtimes):
                is_working = True
            # 沒在班表 → False
            elif current_date.weekday() not in schedule_weekdays:
                is_working = False
            # # 在班表但有請假 → False
            # elif any(leave.start_day <= current_date <= leave.end_day for leave in leaves):
            #     is_working = False
            # 其他情況就是 True (正常上班日)
            else:
                is_working = True

            if is_working:
                streak += 1
            else:
                streak = 0

            if streak >= 7:
                over = True

            current_date += timedelta(days=1)

        return over


    def check_time_valid_or_overlap(self, rec):
        # 將加班開始跟結束時間轉換成小時
        request_start_half_hour = float(rec.hour_from) + float(rec.min_from)
        request_end_half_hour = float(rec.hour_to) + float(rec.min_to)

        if request_end_half_hour < request_start_half_hour:
            raise UserError(_("開始時間不可大於結束時間"))


        all_overtime = rec.env['starrylord.overtime.apply'].search([('employee_id', '=', rec.employee_id.id),
                                                                    ('start_day', '=', rec.start_day),
                                                                    ('id', '!=', rec.id),
                                                                    ('state', '!=', 'draft'),
                                                                    ('state', '!=', 'refused')])

        in_time_overtime = all_overtime.filtered(lambda x: (
                (float(x.hour_from) + float(x.min_from)) < request_end_half_hour
                and (float(x.hour_to) + float(x.min_to)) > request_start_half_hour))
        if in_time_overtime:
            error_msg = '已於同日 \n'
            for in_time in in_time_overtime:
                error_msg += '單號' + in_time.name + '加班單 ' + str(in_time.hour_from) + '點至' + str(
                    in_time.hour_to) + '點加班\n'
            raise UserError(_("加班時間不可重複\n" + error_msg))


    def to_f_approve(self):
        for rec in self:
            self.check_overtime_time_min_unit(rec)
            # 檢查有無員工id跟開始日期
            if rec.employee_id and rec.start_day:
                self.check_time_valid_or_overlap(rec)
            if self.check_duty_over_6days():
                raise UserError('已連續 7 天上班，違反勞基法！')

            rec.state = 'f_approve'

    def to_draft(self):
        for rec in self:
            # 檢查是否有補休分配被請假申請使用
            if rec.sl_holiday_allocation_ids:
                for allocation in rec.sl_holiday_allocation_ids:
                    used_records = self.env['starrylord.holiday.used.record'].search([
                        ('holiday_allocation_id', '=', allocation.id)
                    ])
                    if used_records:
                        raise UserError(
                            "無法撤銷此加班單，因為產生的補休時數已被以下請假申請使用：\n"
                                "請先撤銷或拒絕相關請假申請後再操作。"
                        )
            rec.sl_holiday_allocation_ids.unlink()
            rec.state = 'draft'

    def to_refused(self):
        for rec in self:
            rec.state = 'refused'
            if rec.sl_holiday_allocation_ids:
                rec.sl_holiday_allocation_ids.unlink()

    # def to_approved(self):
    #     for rec in self:
    #         rec.state = 'approved'

    def agree(self):
        for rec in self:
            self.check_overtime_time_min_unit(rec)
            self.check_time_valid_or_overlap(rec)
            if self.check_duty_over_6days():
                raise UserError('已連續 7 天上班，違反勞基法！')

            rec.state = 'agree'
            rec.hr_confirm_state = 'pending'

            # 只建立加班行事曆（保留）
            start_date = rec.merge_date_time(
                rec.start_day,
                float(rec.hour_from) + float(rec.min_from)
            )

            if rec.hour_to == '24':
                end_day = rec.start_day + relativedelta(days=1)
                end_time_float = float(rec.min_to)
            else:
                end_day = rec.start_day
                end_time_float = float(rec.hour_to) + float(rec.min_to)

            end_date = rec.merge_date_time(end_day, end_time_float)

            rec.hr_personal_calendar_id = self.env['hr.personal.calendar'].create({
                'employee_id': rec.employee_id.id,
                'date_type': 'overtime',
                'calendar_date': start_date,
                'start_date': start_date,
                'end_date': end_date,
            }).id


    # 20251219 添加人力資源人員的處理按鈕
    # 按鈕：未符合
    def action_hr_invalid(self):
        self.ensure_one()

        if self.state != 'agree':
            raise UserError('僅限主管已確認的加班單，才能進行人資確認')

        return {
            'type': 'ir.actions.act_window',
            'name': '人資未符合說明',
            'res_model': 'starrylord.overtime.hr.invalid.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_overtime_apply_id': self.id,
            }
        }

    # 準備行為
    def _prepare_holiday_allocation_from_overtime(self):
        """
        將加班時數正確拋轉為補休分配
        規則：
        1. 先依補休假別取得 request_unit (time_type)
        2. 再依 time_type 寫入正確的分鐘欄位
        3. 不更動既有欄位結構
        """
        self.ensure_one()

        # 取得補休假別
        setting = self.env['ir.config_parameter'].sudo()
        holiday_comp_id = int(setting.get_param('sl_hrm_holiday.holiday_comp_id', default=False))
        if not holiday_comp_id:
            return False

        holiday_type = self.env['starrylord.holiday.type'].browse(holiday_comp_id)
        time_type = holiday_type.request_unit  # hour / half / quarter / day

        # 拆解加班時數（小時制）
        total = round(self.duration_time, 2)
        hour_part = int(total)
        minute_part = round(total - hour_part, 2)

        allocation_data = {
            'holiday_type_id': holiday_comp_id,
            'sl_overtime_apply_id': self.id,
            'employee_id': self.employee_id.id,
            'year': str(self.start_day.year),
            'duration_time': hour_part,
            'validity_start': date.today() + relativedelta(
                day=1,
                month=self.start_day.month,
                year=self.start_day.year
            ),
            'validity_end': self.allocation_validity_end,
        }

        # 分鐘單位正規化（只允許系統可接受的值）
        if minute_part > 0:
            if time_type == 'half':
                # half 只允許 0 或 0.5
                allocation_data['duration_min'] = '0.5' if minute_part >= 0.5 else '0'
            else:
                # hour / quarter / day → 使用 duration_min_quarter
                minute_key = {
                    0.25: '0.25',
                    0.5: '0.5',
                    0.75: '0.75',
                }.get(round(minute_part, 2))
                if minute_key:
                    allocation_data['duration_min_quarter'] = minute_key

        return allocation_data



    # 按鈕：確認加班
    def action_hr_confirm(self):
        for rec in self:
            if rec.state != 'agree':
                raise UserError('加班單尚未主管確認')
            if rec.hr_confirm_state != 'pending':
                raise UserError('此加班單已完成確認')

            rec.hr_confirm_state = 'confirmed'

            # 只有補休才建立分配
            if rec.type != 'holiday':
                continue

            allocation_data = rec._prepare_holiday_allocation_from_overtime()
            if allocation_data:
                rec.write({
                    'sl_holiday_allocation_ids': [(0, 0, allocation_data)]
                })


class HrAttendanceCheck(models.Model):
    _inherit = 'hr.attendance.check'

    overtime_apply_ids = fields.Many2many(
        comodel_name='starrylord.overtime.apply',
        string='加班單'
    )

    overtime_time_summary = fields.Char(
        string='加班時段',
        compute='_compute_overtime_time_summary',
        store=True
    )

    @api.depends(
        'overtime_apply_ids.hour_from',
        'overtime_apply_ids.min_from',
        'overtime_apply_ids.hour_to',
        'overtime_apply_ids.min_to',
        'overtime_apply_ids.state'
    )
    def _compute_overtime_time_summary(self):
        for rec in self:
            parts = []

            for ot in rec.overtime_apply_ids.filtered(lambda x: x.state == 'agree'):
                if not all([ot.hour_from, ot.min_from, ot.hour_to, ot.min_to]):
                    continue

                start_h = int(ot.hour_from)
                start_m = int(float(ot.min_from) * 60)
                end_h = int(ot.hour_to)
                end_m = int(float(ot.min_to) * 60)

                start = f"{start_h:02d}:{start_m:02d}"
                end = f"{end_h:02d}:{end_m:02d}"

                parts.append(f"{start}~{end}")

            if parts:
                rec.overtime_time_summary = f"加班：{' / '.join(parts)}"
            else:
                rec.overtime_time_summary = ''


class StarryLordOvertimeComplianceWizard(models.TransientModel):
    _name = 'starrylord.overtime.compliance.wizard'
    _description = '加班合規判斷'

    overtime_apply_id = fields.Many2one(
        'starrylord.overtime.apply',
        string='加班單',
        required=True
    )

    compliance_state = fields.Selection(
        [
            ('ok', '合規'),
            ('ng', '不合規'),
        ],
        string='合規判斷',
        required=True
    )

    compliance_reason = fields.Text(
        string='不合規原因'
    )

    @api.onchange('compliance_state')
    def _onchange_compliance_state(self):
        if self.compliance_state == 'ok':
            self.compliance_reason = False

    def action_confirm(self):
        self.ensure_one()

        if self.compliance_state == 'ng' and not self.compliance_reason:
            raise UserError('請填寫不合規原因')

        self.overtime_apply_id.write({
            'compliance_state': self.compliance_state,
            'compliance_reason': self.compliance_reason if self.compliance_state == 'ng' else False,
        })


class StarryLordOvertimeAttendanceAdjustWizard(models.TransientModel):
    _name = 'starrylord.overtime.attendance.adjust.wizard'
    _description = '加班異常處理'

    overtime_apply_id = fields.Many2one(
        'starrylord.overtime.apply',
        string='加班單',
        required=True
    )

    # === 處理模式 ===
    adjust_mode = fields.Selection(
        [
            ('approve', '依核准時間'),
            ('attendance', '依打卡時間'),
            ('manual', '手動調整'),
        ],
        string='處理模式',
        required=True,
        default='approve'
    )

    # === 可選打卡紀錄（來源：加班單上的 m2m）===
    attendance_id = fields.Many2one(
        'hr.attendance',
        string='打卡紀錄',
        domain="[('id', 'in', attendance_ids)]"
    )

    attendance_ids = fields.Many2many(
        'hr.attendance',
        string='打卡紀錄',
        readonly=True
    )

    # === 調整後時間 ===
    adjust_hour_from = fields.Selection(
        selection=lambda self: self.env['starrylord.overtime.apply']._get_hour_selection(),
        string='開始小時'
    )
    adjust_min_from = fields.Selection(
        [('0', '00'), ('0.25', '15'), ('0.5', '30'), ('0.75', '45')],
        string='開始分鐘'
    )
    adjust_hour_to = fields.Selection(
        selection=lambda self: self.env['starrylord.overtime.apply']._get_hour_selection(end=True),
        string='結束小時'
    )
    adjust_min_to = fields.Selection(
        [('0', '00'), ('0.25', '15'), ('0.5', '30'), ('0.75', '45')],
        string='結束分鐘'
    )

    adjust_duration_time = fields.Float(
        string='調整後加班時長',
        compute='_compute_duration',
        store=True
    )

    adjust_memo = fields.Char(string='調整說明')

    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)

        overtime_apply_id = self.env.context.get('default_overtime_apply_id')
        if not overtime_apply_id:
            return res

        overtime = self.env['starrylord.overtime.apply'].browse(overtime_apply_id)

        if 'attendance_ids' in fields_list:
            res['attendance_ids'] = [(6, 0, overtime.attendance_ids.ids)]

        return res


    # === 模式切換時自動填值 ===
    @api.onchange('adjust_mode', 'attendance_id')
    def _onchange_adjust_mode(self):
        ot = self.overtime_apply_id

        # 依核准時間
        if self.adjust_mode == 'approve':
            self.adjust_hour_from = ot.hour_from
            self.adjust_min_from = ot.min_from
            self.adjust_hour_to = ot.hour_to
            self.adjust_min_to = ot.min_to
            self._compute_duration()

        # === 手動調整：預設也帶入原始核准時間 ===
        elif self.adjust_mode == 'manual':
            self.adjust_hour_from = ot.hour_from
            self.adjust_min_from = ot.min_from
            self.adjust_hour_to = ot.hour_to
            self.adjust_min_to = ot.min_to
            self._compute_duration()

        # 依打卡時間（保守）
        elif self.adjust_mode == 'attendance' and self.attendance_id:
            check_in = self.attendance_id.check_in + timedelta(hours=8)
            check_out = self.attendance_id.check_out + timedelta(hours=8)

            # 開始時間：往後補齊到 30 分
            start_min = 30 if check_in.minute > 0 else 0
            self.adjust_hour_from = str(check_in.hour)
            self.adjust_min_from = '0.5' if start_min == 30 else '0'

            # 結束時間：往前補齊到 30 分
            end_min = 30 if check_out.minute >= 30 else 0
            self.adjust_hour_to = str(check_out.hour)
            self.adjust_min_to = '0.5' if end_min == 30 else '0'

            self._compute_duration()

    @api.depends(
        'adjust_hour_from',
        'adjust_min_from',
        'adjust_hour_to',
        'adjust_min_to'
    )
    def _compute_duration(self):
        if not all([
            self.adjust_hour_from,
            self.adjust_min_from,
            self.adjust_hour_to,
            self.adjust_min_to
        ]):
            self.adjust_duration_time = 0
            return

        start = float(self.adjust_hour_from) + float(self.adjust_min_from)
        end = float(self.adjust_hour_to) + float(self.adjust_min_to)
        self.adjust_duration_time = max(end - start, 0)

    # === 確認寫回 ===
    def action_confirm(self):
        self.ensure_one()
        # 強制確保最新計算
        self._compute_duration()
        ot = self.overtime_apply_id

        ot.write({
            'adjust_hour_from': self.adjust_hour_from,
            'adjust_min_from': self.adjust_min_from,
            'adjust_hour_to': self.adjust_hour_to,
            'adjust_min_to': self.adjust_min_to,
            'adjust_duration_time': self.adjust_duration_time,
            'overtime_attendance_process_state': 'done',
            'overtime_adjust_memo': self.adjust_memo,
        })


class StarryLordOvertimeHrInvalidWizard(models.TransientModel):
    _name = 'starrylord.overtime.hr.invalid.wizard'
    _description = '人資未符合原因填寫'

    overtime_apply_id = fields.Many2one(
        'starrylord.overtime.apply',
        string='加班單',
        required=True
    )

    hr_invalid_reason = fields.Text(
        string='未符合原因',
        required=True
    )

    def action_confirm(self):
        self.ensure_one()

        self.overtime_apply_id.write({
            'hr_confirm_state': 'invalid',
            'hr_invalid_reason': self.hr_invalid_reason,
        })
