from dateutil.relativedelta import relativedelta

from odoo import models, fields, api, _
from datetime import date, timedelta, datetime, time
import pytz


class HrAttendanceCheck(models.Model):
    _name = 'hr.attendance.check'
    _description = '出勤記錄表'
    _order = 'date desc, employee_number'
    _rec_name = 'display_name'

    display_name = fields.Char(string='顯示名稱', compute='_compute_display_name')
    date = fields.Date(string='日期', required=True)
    day_of_week = fields.Selection(
        selection=[
            ('0', '一'),
            ('1', '二'),
            ('2', '三'),
            ('3', '四'),
            ('4', '五'),
            ('5', '六'),
            ('6', '日'),
        ],
        string='星期',
        compute='_compute_worktime'
    )
    employee_id = fields.Many2one('hr.employee.public', string='員工', required=True)
    is_no_need_check_in = fields.Boolean(
        string='無需打卡',
        related='employee_id.employee_id.is_no_need_check_in',
        readonly=True
    )
    user_id = fields.Many2one('res.users', string='User', related='employee_id.user_id', related_sudo=True,
                              compute_sudo=True, store=True, readonly=True)
    # schedule_id = fields.Many2one('hr.schedule', related='employee_id.schedule_id', string='班別')
    employee_number = fields.Char(string='員工編號', related='employee_id.employee_id.employee_number', store=True, related_sudo=True)
    department_id = fields.Many2one('hr.department', string="部門", store=True,
                                    related="employee_id.department_id")
    job_id = fields.Many2one('hr.job', string="職稱", related="employee_id.job_id", store=True, related_sudo=True)
    work_check_check_in_str = fields.Char(string="打卡", compute='_compute_worktime')
    work_check_check_out_str = fields.Char(string="打卡", compute='_compute_worktime')
    work_worktime_start_str = fields.Char(string="上班", compute='_compute_worktime')
    work_worktime_end_str = fields.Char(string="下班", compute='_compute_worktime')
    work_check_start_str = fields.Char(string="上班/打卡", compute='_compute_worktime')
    work_check_end_str = fields.Char(string="下班/打卡", compute='_compute_worktime')
    # work_start = fields.Datetime(string="上班時間", required=False, )
    # work_end = fields.Datetime(string="下班時間", required=False, )
    # check_start = fields.Datetime(string="上班打卡時間", required=False, )
    # check_end = fields.Datetime(string="下班打卡時間", required=False, )
    work_memo = fields.Char(string="出勤異常說明", compute='_compute_worktime')
    holiday_memo = fields.Char(string="請假說明", compute='_compute_worktime')
    time_diff = fields.Char(string="時數", compute='_compute_worktime')
    holiday_id = fields.Many2one('starrylord.holiday.apply', string="請假", required=False, store=True)
    # overtime_id 欄位已移至 sl_hrm_overtime 模組以避免循環依賴
    # overtime_id = fields.Many2one('starrylord.overtime.apply', string="加班", required=False, )

    memo5 = fields.Char(string="備註", required=False, )
    memo6 = fields.Char(string="審核備註", required=False, )
    warning_id = fields.Selection(selection=[('0', '無異常'), ('1', '異常')], string="重要警告", required=False, default='0')

    sl_attendance_repair_ids = fields.One2many(
        comodel_name='sl.attendance.repair',
        inverse_name='sl_attendance_check_id',
        string='出勤異常說明單'
    )

    # 20260118 添加正常上班與加班的拆開的紀錄

    # ========= 正常出勤 =========
    normal_work_start_str = fields.Char(
        string="正常上班時間",
        compute="_compute_attendance_segments"
    )
    normal_work_end_str = fields.Char(
        string="正常下班時間",
        compute="_compute_attendance_segments"
    )
    normal_check_in_str = fields.Char(
        string="正常上班開始",
        compute="_compute_attendance_segments"
    )
    normal_check_out_str = fields.Char(
        string="正常下班結束",
        compute="_compute_attendance_segments"
    )
    normal_check_start_str = fields.Char(
        string="正常上班（規則/實際）",
        compute="_compute_attendance_segments"
    )
    normal_check_end_str = fields.Char(
        string="正常下班（規則/實際）",
        compute="_compute_attendance_segments"
    )

    # ========= 加班 =========
    overtime_work_start_str = fields.Char(
        string="加班起算時間",
        compute="_compute_attendance_segments"
    )
    overtime_check_in_str = fields.Char(
        string="加班上班開始",
        compute="_compute_attendance_segments"
    )
    overtime_check_out_str = fields.Char(
        string="加班下班結束",
        compute="_compute_attendance_segments"
    )
    overtime_check_start_str = fields.Char(
        string="加班上班（規則/實際）",
        compute="_compute_attendance_segments"
    )
    overtime_check_end_str = fields.Char(
        string="加班下班",
        compute="_compute_attendance_segments"
    )
    # ========= 新的出勤異常欄位 =========
    attendance_anomaly_str = fields.Char(
        string="出勤異常（新）",
        compute="_compute_attendance_anomaly"
    )

    attendance_anomaly_level = fields.Selection(
        [
            ('0', '正常'),
            ('1', '異常'),
        ],
        string="出勤狀態（新）",
        compute="_compute_attendance_anomaly"
    )

    # 20260118 正常上班與加班分開的計算

    def _compute_attendance_segments(self):
        for rec in self:
            # ---------- 初始化 ----------
            rec.normal_work_start_str = ''
            rec.normal_work_end_str = ''
            rec.normal_check_in_str = ''
            rec.normal_check_out_str = ''
            rec.normal_check_start_str = ''
            rec.normal_check_end_str = ''

            rec.overtime_work_start_str = ''
            rec.overtime_check_in_str = ''
            rec.overtime_check_out_str = ''
            rec.overtime_check_start_str = ''
            rec.overtime_check_end_str = ''

            if not rec.employee_id or not rec.date:
                continue

            user_tz = self.env.user.tz or 'UTC'
            local_tz = pytz.timezone(user_tz)

            # ===== 當日開始 =====
            day_start_local = local_tz.localize(
                datetime.combine(rec.date, time.min)
            )

            # ===== 判斷國定假日 =====
            is_holiday = bool(self.env['hr.public.holiday'].sudo().search([
                ('date', '=', rec.date),
                ('holiday_type', '=', 'holiday')
            ], limit=1))

            # ===== 班表時間 =====
            work_start_local = None
            work_end_local = None
            work_start_str = ''
            work_end_str = ''

            if not is_holiday and rec.employee_id.schedule_id:
                worktime = self.env['hr.schedule.worktime'].sudo().search([
                    ('worktime_id', '=', rec.employee_id.schedule_id.id),
                    ('dayofweek', '=', rec.date.weekday()),
                    ('date_type', '=', 'schedule')
                ], limit=1)

                if worktime:
                    work_start_str = self.convert_float_time_to_string(worktime.work_start)
                    work_end_str = self.convert_float_time_to_string(worktime.work_end)

                    work_start_local = local_tz.localize(
                        datetime.combine(rec.date, datetime.strptime(work_start_str, "%H:%M").time())
                    )
                    work_end_local = local_tz.localize(
                        datetime.combine(rec.date, datetime.strptime(work_end_str, "%H:%M").time())
                    )

            # ===== 跨天加班截止（制度）=====
            if work_end_local:
                overtime_end_local = work_end_local + timedelta(hours=8)
            else:
                overtime_end_local = local_tz.localize(
                    datetime.combine(rec.date + timedelta(days=1), time(hour=6, minute=0))
                )

            # ===== UTC 轉換 =====
            day_start_utc = day_start_local.astimezone(pytz.UTC)
            overtime_end_utc = overtime_end_local.astimezone(pytz.UTC)

            # ===== 規則時間顯示 =====
            rec.normal_work_start_str = '國定假日' if is_holiday else (work_start_str or '無')
            rec.normal_work_end_str = '國定假日' if is_holiday else (work_end_str or '無')
            rec.overtime_work_start_str = '國定假日' if is_holiday else (work_end_str or '無')

            # ===== 抓打卡資料 =====
            attendance_model = self.env['hr.attendance']

            check_in_records = attendance_model.search([
                ('employee_id', '=', rec.employee_id.id),
                ('check_in', '>=', day_start_utc),
                ('check_in', '<=', overtime_end_utc),
            ])

            check_out_records = attendance_model.search([
                ('employee_id', '=', rec.employee_id.id),
                ('check_out', '>=', day_start_utc),
                ('check_out', '<=', overtime_end_utc),
            ])

            check_ins = [
                pytz.UTC.localize(att.check_in).astimezone(local_tz)
                for att in check_in_records if att.check_in
            ]
            check_outs = [
                pytz.UTC.localize(att.check_out).astimezone(local_tz)
                for att in check_out_records if att.check_out
            ]

            check_ins.sort()
            check_outs.sort()

            last_check_out = check_outs[-1] if check_outs else None

            # ===== 正常上班開始 =====
            normal_check_in = None
            if not is_holiday and work_end_local:
                for ci in check_ins:
                    if ci <= work_end_local:
                        normal_check_in = ci
                        break

            # ===== 正常下班結束（初始）=====
            normal_check_out = None
            if not is_holiday and work_end_local:
                for co in check_outs:
                    if co >= work_end_local:
                        normal_check_out = co
                        break

            # ===== 加班上班開始（分段型）=====
            overtime_check_in = None
            if check_ins:
                if is_holiday:
                    overtime_check_in = check_ins[0]
                elif work_end_local:
                    for ci in check_ins:
                        if ci > work_end_local:
                            overtime_check_in = ci
                            break

            # ===== 是否「應該有加班紀錄」=====
            should_have_overtime = False
            if work_end_local and last_check_out:
                if last_check_out > (work_end_local + timedelta(minutes=30)):
                    should_have_overtime = True

            # ===== 加班下班結束 =====
            overtime_check_out = None
            if overtime_check_in:
                for co in check_outs:
                    if co > overtime_check_in:
                        overtime_check_out = co
                        break

            # ===== 延伸型加班處理 =====
            if should_have_overtime and not overtime_check_in and last_check_out:
                normal_check_out = None
                overtime_check_out = last_check_out

            # ===== 寫回字串 =====
            rec.normal_check_in_str = normal_check_in.strftime('%H:%M') if normal_check_in else '無'
            rec.normal_check_out_str = normal_check_out.strftime('%H:%M') if normal_check_out else '無'
            rec.overtime_check_in_str = overtime_check_in.strftime('%H:%M') if overtime_check_in else '無'
            rec.overtime_check_out_str = overtime_check_out.strftime('%H:%M') if overtime_check_out else '無'

            # ===== 組合呈現 =====
            rec.normal_check_start_str = f"{rec.normal_work_start_str} / {rec.normal_check_in_str}"
            rec.normal_check_end_str = f"{rec.normal_work_end_str} / {rec.normal_check_out_str}"

            if overtime_check_in:
                rec.overtime_check_start_str = f"{rec.overtime_work_start_str} / {rec.overtime_check_in_str}"
                rec.overtime_check_end_str = rec.overtime_check_out_str
            else:
                rec.overtime_check_start_str = f"{rec.overtime_work_start_str} / 無"
                rec.overtime_check_end_str = rec.overtime_check_out_str or '無'

    # =================================================
    # 新的出勤異常計算（只依賴正常/加班四個欄位）
    # =================================================
    @api.depends(
        'normal_check_start_str',
        'normal_check_end_str',
        'overtime_check_start_str',
        'overtime_check_end_str',
    )
    def _compute_attendance_anomaly(self):
        for rec in self:
            anomalies = []
            flags = []  # 非異常提示（如：有加班時間）
            rec.attendance_anomaly_str = ''
            rec.attendance_anomaly_level = '0'

            # ===============================
            # 正常上班異常
            # ===============================
            if rec.normal_check_start_str:
                try:
                    rule, actual = rec.normal_check_start_str.split(' / ')
                except ValueError:
                    rule, actual = None, None

                if rule and rule not in ('無', '國定假日'):
                    if actual == '無':
                        anomalies.append('上班未刷卡')
                    else:
                        try:
                            rule_t = datetime.strptime(rule, '%H:%M').time()
                            actual_t = datetime.strptime(actual, '%H:%M').time()
                            if actual_t > rule_t:
                                anomalies.append('遲到')
                        except Exception:
                            pass

            # ===============================
            # 提早出勤（提示，不算異常）
            # 正常上班前 4 小時 ~ 30 分鐘
            # ===============================
            if rec.normal_check_start_str:
                try:
                    rule, actual = rec.normal_check_start_str.split(' / ')
                except ValueError:
                    rule, actual = None, None

                if rule and actual and rule not in ('無', '國定假日') and actual != '無':
                    try:
                        rule_t = datetime.strptime(rule, '%H:%M').time()
                        actual_t = datetime.strptime(actual, '%H:%M').time()

                        rule_dt = datetime.combine(rec.date, rule_t)
                        actual_dt = datetime.combine(rec.date, actual_t)

                        if (
                            rule_dt - timedelta(hours=4)
                            <= actual_dt
                            < rule_dt - timedelta(minutes=30)
                        ):
                            flags.append('提早出勤')
                    except Exception:
                        pass
            # ===============================
            # 正常下班異常
            # ===============================
            if rec.normal_check_end_str:
                try:
                    rule, actual = rec.normal_check_end_str.split(' / ')
                except ValueError:
                    rule, actual = None, None

                if rule and rule not in ('無', '國定假日'):
                    if actual == '無':
                        anomalies.append('下班未刷卡')
                    else:
                        try:
                            rule_t = datetime.strptime(rule, '%H:%M').time()
                            actual_t = datetime.strptime(actual, '%H:%M').time()
                            if actual_t < rule_t:
                                anomalies.append('早退')
                        except Exception:
                            pass

            # ===============================
            # 加班結構判斷
            # ===============================
            has_overtime_end = bool(
                rec.overtime_check_end_str
                and rec.overtime_check_end_str not in ('無', '國定假日')
            )

            if has_overtime_end:
                flags.append('有加班時間')

            # ===============================
            # 加班異常（制度不完整）
            # ===============================
            if has_overtime_end:
                # 解析加班上班
                try:
                    _, overtime_actual = rec.overtime_check_start_str.split(' / ')
                except Exception:
                    overtime_actual = None

                # 延伸型加班：有結束，沒開始
                if not overtime_actual or overtime_actual == '無':
                    anomalies.append('加班上班未刷卡')

            # ===============================
            # 組合結果
            # ===============================
            result = []

            if anomalies:
                result.extend(anomalies)
                rec.attendance_anomaly_level = '1'

            if flags:
                result.extend(flags)

            if result:
                rec.attendance_anomaly_str = ' '.join(dict.fromkeys(result))
            else:
                rec.attendance_anomaly_str = '正常'
                rec.attendance_anomaly_level = '0'

    def _compute_display_name(self):
        for rec in self:
            # 顯示date的日期字串
            rec.display_name = '%s - %s' % (rec.employee_id.name, rec.date)

    def convert_float_time_to_string(self, time_float):
        if time_float is None:
            return None
        hours = int(time_float)
        minutes = int((time_float - hours) * 60)
        return f"{hours:02d}:{minutes:02d}"

    # 計算上下班.簽到退及填入相關備註
    def _compute_worktime(self):
        for rec in self:
            rec.warning_id = '0'
            rec.work_memo = ''
            rec.holiday_memo = ''
            # 依固定班表計算
            
            user_tz = self.env.user.tz or 'UTC'
            local_tz = pytz.timezone(user_tz)
            holiday_model = self.env['hr.public.holiday']
            
            current = rec.date
            rec.day_of_week = str(current.weekday())
            start_datetime_local = datetime.combine(current, time.min)
            end_datetime_local = datetime.combine(current, time.max)

            start_datetime_utc_str = holiday_model.datetime_convert(start_datetime_local)
            end_datetime_utc_str = holiday_model.datetime_convert(end_datetime_local)

            if not rec.employee_id.schedule_id.is_user_personal_calendar:
                worktime = self.env['hr.schedule.worktime'].sudo().search(
                    [('worktime_id', '=', rec.employee_id.schedule_id.id),
                     # ('date_type', '=', 'schedule'),
                     ('dayofweek', '=', current.weekday()),
                     ])
                # 判斷是否為國定假日或補班日
                public_holiday = self.env['hr.public.holiday'].sudo().search([('date', '=', current), ('holiday_type', 'in', ['holiday', 'make_up_day'])])
                if public_holiday:
                    if public_holiday.holiday_type == 'holiday':
                        work_start = '國定假日'
                        work_end = '國定假日'
                        earliest_work_start_local = None
                        latest_work_end_local = None
                    elif public_holiday.holiday_type == 'make_up_day':
                        make_up_worktime = self.env['hr.schedule.worktime'].sudo().search(
                            [('worktime_id', '=', rec.employee_id.schedule_id.id),
                             ('date_type', '=', 'schedule'),
                             ('dayofweek', '=', current.weekday() -1),
                             ])
                        work_start = self.convert_float_time_to_string(make_up_worktime.work_start)
                        work_end = self.convert_float_time_to_string(make_up_worktime.work_end)
                        earliest_work_start_local = local_tz.localize(
                            datetime.combine(current, datetime.strptime(work_start, "%H:%M").time()))
                        latest_work_end_local = local_tz.localize(
                            datetime.combine(current, datetime.strptime(work_end, "%H:%M").time()))
                else:
                    if worktime:
                        if worktime.date_type == 'schedule':
                            work_start = self.convert_float_time_to_string(worktime.work_start)
                            work_end = self.convert_float_time_to_string(worktime.work_end)
                            earliest_work_start_local = local_tz.localize(
                                datetime.combine(current, datetime.strptime(work_start, "%H:%M").time()))
                            latest_work_end_local = local_tz.localize(
                                datetime.combine(current, datetime.strptime(work_end, "%H:%M").time()))
                        elif worktime.date_type == 'day_off':
                            work_start = '休假日'
                            work_end = '休假日'
                            earliest_work_start_local = None
                            latest_work_end_local = None
                        elif worktime.date_type == 'regular_holiday':
                            work_start = '例假日'
                            work_end = '例假日'
                            earliest_work_start_local = None
                            latest_work_end_local = None

                    else:
                        work_start = '班表未設定'
                        work_end = '班表未設定'
                        earliest_work_start_local = None
                        latest_work_end_local = None

            else:
                work_start = '班表未設定'
                work_end = '班表未設定'
                earliest_work_start_local = None
                latest_work_end_local = None

            # 打卡記錄
            attendance_ids_checkin = rec.env['hr.attendance'].search([('employee_id', '=', rec.employee_id.id),
                                                                      ('check_in', '>=', start_datetime_utc_str),
                                                                      ('check_in', '<=', end_datetime_utc_str)])
            attendance_ids_checkout = rec.env['hr.attendance'].search([('employee_id', '=', rec.employee_id.id),
                                                                       ('check_out', '>=', start_datetime_utc_str),
                                                                       ('check_out', '<=', end_datetime_utc_str)])
                
            # 初始化為 None
            earliest_check_in = None
            latest_check_out = None

            # 搜索最早的 check_in
            for attendance in attendance_ids_checkin:
                if earliest_check_in is None or attendance.check_in < earliest_check_in:
                    earliest_check_in = attendance.check_in

            # 搜索最晚的 check_out
            for attendance in attendance_ids_checkout:
                if attendance.check_out and (latest_check_out is None or attendance.check_out > latest_check_out):
                    latest_check_out = attendance.check_out
                # if attendance.checkout_message:
                #     rec.memo5 = attendance.checkout_message

            # 转换 UTC -> 本地时间
            earliest_check_in_local = pytz.UTC.localize(earliest_check_in).astimezone(
                local_tz) if earliest_check_in else None
            latest_check_out_local = pytz.UTC.localize(latest_check_out).astimezone(
                local_tz) if latest_check_out else None

            # 格式化为字符串
            check_in_str = earliest_check_in_local.strftime('%H:%M:%S') if earliest_check_in_local else '無打卡記錄'
            check_out_str = latest_check_out_local.strftime('%H:%M:%S') if latest_check_out_local else '無打卡記錄'


            # 檢查是否有已同意的補卡說明單
            repair_approved_list = self.env['sl.attendance.repair'].search([
                ('employee_id', '=', rec.employee_id.id),
                ('sl_attendance_check_id', '=', rec.id),
                ('state', '=', 'agree')
            ])
            
            repair_approved = {'hour_from': None, 'min_from': None, 'hour_to': None, 'min_to': None}
            row_compare = {'from': '9999', 'to': ''}
            for row in repair_approved_list:
                row_from = (str(row.hour_from) if row.hour_from else '99') + (str(row.min_from) if row.min_from else '99')
                row_to = (str(row.hour_to) if row.hour_to else '') + (str(row.min_to) if row.min_to else '')
                if row_from < row_compare['from']:
                    row_compare['from'] = row_from
                    repair_approved['hour_from'] = row.hour_from
                    repair_approved['min_from'] = row.min_from
                if row_to > row_compare['to']:
                    row_compare['to'] = row_to
                    repair_approved['hour_to'] = row.hour_to
                    repair_approved['min_to'] = row.min_to
                
            if repair_approved_list:
                if repair_approved['hour_from'] not in (None, '', False) and repair_approved['min_from'] not in (None, '', False):
                    # rec.work_memo += '已補上班卡 '
                    hour_from = int(repair_approved['hour_from'])
                    min_from = int(repair_approved['min_from'])
                    check_in_str = f'{hour_from:02d}:{min_from:02d}:00'
                    check_in_time = datetime.strptime(check_in_str, "%H:%M:%S").time()
                    check_in_datetime = datetime.combine(rec.date, check_in_time)
                    earliest_check_in_local = local_tz.localize(check_in_datetime)
                if repair_approved['hour_to'] not in (None, '', False) and repair_approved['min_to'] not in (None, '', False):
                    # rec.work_memo += '已補下班卡 '
                    hour_to = int(repair_approved['hour_to'])
                    min_to = int(repair_approved['min_to'])
                    check_out_str = f'{hour_to:02d}:{min_to:02d}:00'
                    check_out_time = datetime.strptime(check_out_str, "%H:%M:%S").time()
                    check_out_datetime = datetime.combine(rec.date, check_out_time)
                    latest_check_out_local = local_tz.localize(check_out_datetime)
            # # 轉換為所需格式的字符串
            # check_in_str = (earliest_check_in+ timedelta(hours=8)).strftime('%H:%M') if earliest_check_in else '__:__'
            # check_out_str = (latest_check_out+ timedelta(hours=8)).strftime('%H:%M') if latest_check_out else '__:__'

            rec.work_check_start_str = '%s / %s' % (work_start, check_in_str)
            rec.work_check_end_str = '%s / %s' % (work_end, check_out_str)
            rec.work_worktime_start_str = '%s' % work_start
            rec.work_check_check_in_str = '%s' % check_in_str
            rec.work_worktime_end_str = '%s' % work_end
            rec.work_check_check_out_str = '%s' % check_out_str

            # 寫入打卡的上班時間
            if earliest_check_in_local is not None and latest_check_out_local is not None:
                am_end = earliest_check_in_local.replace(hour=int(worktime['am_end']))
                pm_start = earliest_check_in_local.replace(hour=int(worktime['pm_start']))
                pm_work_start = max(pm_start, earliest_check_in_local) # 有可能午休後才來上班
                total_seconds = 0
                
                time_diff1 = am_end - earliest_check_in_local
                if time_diff1 > timedelta(0):
                    total_seconds += time_diff1.total_seconds()
                time_diff2 = latest_check_out_local - pm_work_start
                if time_diff2 > timedelta(0):
                    total_seconds += time_diff2.total_seconds()

                hours = int(total_seconds // 3600)
                minutes = int((total_seconds % 3600) // 60)

                rec.time_diff = f'{hours} h {minutes} m'
            else:
                rec.time_diff = ''

            # 判斷遲到早退
            adjusted_work_start = earliest_work_start_local
            adjusted_work_end = latest_work_end_local
            full_in_leave = False

            leave_records = self.env['starrylord.holiday.apply'].search([
                ('employee_id', '=', rec.employee_id.id),
                ('apply_from', '<=', rec.date + timedelta(days=1) - timedelta(seconds=1)),
                ('apply_to', '>=', rec.date),
                ('state', '=', 'agree')
            ])

            # 如果當天有請假，檢查是否需要延後上班時間
            for leave in leave_records:
                    # 延後上班時間為請假的結束時間（只取時間部分）
                leave_from_local = pytz.UTC.localize(leave.apply_from).astimezone(local_tz)
                leave_to_local = pytz.UTC.localize(leave.apply_to).astimezone(local_tz)
                rec.holiday_memo += f'{leave.holiday_allocation_id.name}: {leave_from_local.strftime("%H:%M")} - {leave_to_local.strftime("%H:%M")}, '
                
                # 只有在 adjusted_work_start 和 adjusted_work_end 不為 None 時才進行比較
                if adjusted_work_start is not None and adjusted_work_end is not None:
                    if leave_from_local.date() == rec.date and leave_from_local <= adjusted_work_start:
                        adjusted_work_start = max(leave_to_local, adjusted_work_start)
                    if leave_to_local.date() == rec.date and leave_to_local <= adjusted_work_end:
                        adjusted_work_end = min(leave_from_local, adjusted_work_end)
                    if ((leave_from_local <= adjusted_work_start and leave_to_local >= adjusted_work_end)
                        or (adjusted_work_start >= adjusted_work_end)):
                        full_in_leave = True
                        break

            if earliest_check_in_local is not None and adjusted_work_start is not None:
                # 允許到當分鐘的 59 秒（例如 9:00:59 仍不算遲到）
                grace = timedelta(seconds=59)
                if earliest_check_in_local > (adjusted_work_start + grace):
                    rec.work_memo += '遲到 '
                    rec.warning_id = '1'

            if latest_check_out_local is not None and adjusted_work_end is not None:
                if latest_check_out_local < adjusted_work_end:
                    rec.work_memo += '早退 '
                    rec.warning_id = '1'

            if earliest_check_in_local is None and adjusted_work_start and not full_in_leave:
                if current <= date.today():
                    rec.work_memo += '上班未刷卡 '
                    rec.warning_id = '1'

            if latest_check_out_local is None and adjusted_work_end and not full_in_leave:
                if current <= date.today():
                    rec.work_memo += '下班未刷卡 '
                    rec.warning_id = '1'

            # 檢查及填入單據
            # 檢查請假記錄
            # 檢查請假記錄（只要有重疊就算）
            holiday = self.env['starrylord.holiday.apply'].search([
                ('employee_id', '=', rec.employee_id.id),
                ('apply_from', '<=', rec.date + timedelta(days=1) - timedelta(seconds=1)),
                ('apply_to', '>=', rec.date),
                ('state', '=', 'agree')
            ], limit=1)
            rec.holiday_id = holiday.id if holiday else False

            # 檢查加班記錄（只要有重疊就算）
            # 此邏輯已移至 sl_hrm_overtime 模組以避免循環依賴
            # overtime_id 欄位由 sl_hrm_overtime 模組提供
            
            if rec.is_no_need_check_in:
                rec.warning_id = '0'
                rec.work_memo = ''
                rec.holiday_memo = ''
            
            
            # 檢查未刷卡記錄
            # attendance_repair = self.env['attendance.repair'].search([
            #     ('employee_id', '=', rec.employee_id.id),
            #     ('start_date', '<=', rec.date),
            #     ('start_date', '>=', rec.date)
            # ], limit=1)

            # rec.attendance_repair_id = attendance_repair.id if attendance_repair else False

    def create_attendance(self, date_start=None):
        # 取得本日date
        today = date.today()
        # today = date(2025, 5, 29)
        print(today)
        attendance_job_days = int(self.env['ir.config_parameter'].sudo().get_param('attendance_job_days', default=3))
        if not date_start:
            date_start = today - timedelta(days=attendance_job_days)
        # date_start = today
        date_end = today

        employee_ids = self.env['hr.employee'].search([('active', '=', True), ('state', '=', 'working'), ('is_no_need_check_in', '=', False)]).ids

        self.create_attendance_records(date_start, date_end, employee_ids)
        self.create_attendance_resign(date_start, date_end)
        
        # 取得action
        action = self.env.ref('sl_hrm.hr_attendance_check_manager_action').read()[0]

        return action

    def create_attendance_resign(self, date_start, date_end):
        # 就算是離職的員工也可能是當天離職，出勤紀錄也要算
        employee_model = self.env['hr.employee']
        employees = employee_model.search([
            '&', ('active', '=', True), ('state', '=', 'resign'), ('resignation_date', '>=', date_start)
        ])

        for employee in employees:
            date_end = min(date_end, employee.resignation_date)
            self.create_attendance_records(date_start, date_end, [employee.id])
            
    def create_attendance_records(self, date_start, date_end, employee_ids):
        """
        給定日期範圍和員工列表，為每位員工在此範圍內創建出勤記錄。
        如果某天已有記錄，則跳過該天。
        """
        date_start_obj = fields.Date.from_string(date_start)
        date_end_obj = fields.Date.from_string(date_end)
        delta = date_end_obj - date_start_obj

        records_to_create = []
        for employee_id in employee_ids:
            for day in range(delta.days + 1):
                date = date_start_obj + timedelta(days=day)
                # 检查是否已存在记录
                if not self.search_count([
                    ('date', '=', date),
                    ('employee_id', '=', employee_id)
                ]):
                    records_to_create.append({
                        'date': date,
                        'employee_id': employee_id
                    })

        if records_to_create:
            self.create(records_to_create)

    def job_create_attendance_records(self):
        # 取得前一天的日期
        date_start = date.today() - timedelta(days=1)
        date_end = date.today()
        # 只包含在職且啟用的員工
        employee_ids = self.env['hr.employee'].search([('state', '=', 'working'), ('is_no_need_check_in', '=', False)]).ids
        self.create_attendance_records(date_start, date_end, employee_ids)

        # for employee_id in employee_ids:
        #     for day in range(delta.days + 1):
        #         date = date_start_obj + timedelta(days=day)
        #         existing_record = self.search([
        #             ('date', '=', date),
        #             ('employee_id', '=', employee_id)
        #         ], limit=1)
        #         if not existing_record:
        #             self.create({
        #                 'date': date,
        #                 'employee_id': employee_id
        #             })

    def _split_time(self, time_str):
        """
        '09:05' -> ('9', '5')
        '18:00' -> ('18', '0')
        '無' / None -> (False, False)
        """
        if not time_str or time_str in ('無', '國定假日'):
            return False, False
        try:
            h, m = time_str.split(':')
            return str(int(h)), str(int(m))
        except Exception:
            return False, False


    def action_create_attendance_repair(self):
        self.ensure_one()

        # ===== 拆正常上班 =====
        _, normal_in = self.normal_check_start_str.split(' / ') if self.normal_check_start_str else (None, None)
        _, normal_out = self.normal_check_end_str.split(' / ') if self.normal_check_end_str else (None, None)

        hour_from, min_from = self._split_time(normal_in)
        hour_to, min_to = self._split_time(normal_out)

        # ===== 拆加班 =====
        _, ot_in = self.overtime_check_start_str.split(' / ') if self.overtime_check_start_str else (None, None)
        ot_hour_from, ot_min_from = self._split_time(ot_in)

        ot_hour_to, ot_min_to = self._split_time(self.overtime_check_end_str)

        return {
            'type': 'ir.actions.act_window',
            'name': '新增出勤異常說明單',
            'res_model': 'sl.attendance.repair',
            'view_mode': 'form',
            'target': 'current',
            'context': {
                'default_employee_id': self.employee_id.id,
                'default_user_id': self.user_id.id if self.user_id else False,
                'default_sl_attendance_check_id': self.id,
                'default_start_date': self.date,

                # ===== 正常上班 =====
                'default_hour_from': hour_from,
                'default_min_from': min_from,
                'default_hour_to': hour_to,
                'default_min_to': min_to,

                # ===== 加班 =====
                'default_ot_hour_from': ot_hour_from,
                'default_ot_min_from': ot_min_from,
                'default_ot_hour_to': ot_hour_to,
                'default_ot_min_to': ot_min_to,
            }
        }

    def cron_send_monthly_attendance_anomaly_notification(self):
        """
        排程任務：每天早上 9 點檢查當月的異常考勤記錄
        並發送通知給管理員和相關員工
        3個工作天後發出 / 當月後續只要一直檢查有異常至次月工日第三天持續發出 ,  接下來次月就不發出
        """
        # 取得本月第一天和今天
        # 若今天不是表定上班日，則不執行排程
        _now = date.today()
        worktime_model = self.env['hr.schedule.worktime'].sudo()
        # 檢查是否存在任何班表在今天有排班（date_type 為 'schedule' 且 dayofweek 與今天一致）
        if not worktime_model.search_count([('date_type', '=', 'schedule'), ('dayofweek', '=', _now.weekday())]):
            return
        # 檢查是否為國定假日，若是則不執行排程
        public_holiday = self.env['hr.public.holiday'].sudo().search([
            ('date', '=', _now),
            ('holiday_type', '=', 'holiday')
        ], limit=1)
        if public_holiday:
            return
        
        today = date.today()
        start_day = today
        offset_days = 3
        while offset_days > 0:
            start_day -= timedelta(days=1)
            # 檢查是否為工作日
            if worktime_model.search_count([('date_type', '=', 'schedule'), ('dayofweek', '=', start_day.weekday())]):
                offset_days -= 1
            public_holiday = self.env['hr.public.holiday'].sudo().search([
                ('date', '=', _now),
                ('holiday_type', '=', 'holiday')
            ], limit=1)
            if public_holiday:
                offset_days += 1  # 國定假日不計入工作日
                
        first_day_of_month = start_day.replace(day=1)
                
        
        # 先搜尋當月的所有記錄（限制範圍，避免掃描全表）
        # 只抓取日期範圍內的記錄，不在這裡過濾 warning_id
        month_records = self.search([
            ('date', '>=', first_day_of_month),
            ('date', '<=', start_day),
        ])
        
        if not month_records:
            return
        
        # 強制重新計算所有 computed 欄位（確保資料是最新的）
        # 這會觸發 _compute_worktime 方法
        month_records._compute_worktime()
        
        # 現在從已計算的記錄中過濾出異常記錄
        anomaly_records = month_records.filtered(lambda r: r.warning_id == '1')
        
        if not anomaly_records:
            # 沒有異常記錄，不發送郵件
            return
        
        # 按員工分組異常記錄
        employee_anomalies = {}
        anomaly_records = anomaly_records.sorted(key=lambda r: (r.employee_id.employee_number or '', r.date))
        for record in anomaly_records:
            employee = record.employee_id
            if employee.id not in employee_anomalies and employee.state == 'working':
                employee_anomalies[employee.id] = {
                    'employee': employee,
                    'records': []
                }
            employee_anomalies[employee.id]['records'].append(record)
        
        # 發送給管理員的匯總郵件
        self._send_manager_notification(employee_anomalies, first_day_of_month, today)
        
        # 發送給每個員工的個人郵件
        for employee_id, data in employee_anomalies.items():
            self._send_employee_notification(data['employee'], data['records'], first_day_of_month, today)
    
    def _send_manager_notification(self, employee_anomalies, start_date, end_date):
        """發送匯總郵件給考勤管理員"""
        # 取得考勤管理員群組的使用者
        manager_group = self.env.ref('hr_attendance.group_hr_attendance_manager', raise_if_not_found=False)
        if not manager_group:
            return
        
        manager_emails = []
        for user in manager_group.users:
            if user.employee_id.work_email:
                manager_emails.append(user.employee_id.work_email)
        
        if not manager_emails:
            return
        
        # 準備郵件內容的數據
        total_anomaly_count = sum(len(data['records']) for data in employee_anomalies.values())
        employee_count = len(employee_anomalies)
        
        # 格式化日期
        start_date_str = start_date.strftime('%Y-%m-%d')
        end_date_str = end_date.strftime('%Y-%m-%d')
        
        # 準備員工異常資料（按員工分組顯示詳細記錄）
        day_names = ['一', '二', '三', '四', '五', '六', '日']
        employee_sections = ''
        
        for emp_id, data in employee_anomalies.items():
            employee = data['employee']
            records = data['records']
            
            # 為每個員工建立一個區塊
            employee_sections += f'''
            <div style="margin-bottom: 30px; border: 1px solid #ddd; border-radius: 5px; overflow: hidden;">
                <div style="background-color: #007bff; color: white; padding: 10px 15px;">
                    <strong>{employee.employee_number or ''}</strong> - {employee.name} 
                    <span style="margin-left: 10px;">({employee.department_id.name if employee.department_id else '-'})</span>
                    <span style="float: right; background-color: #d9534f; padding: 3px 10px; border-radius: 3px; font-size: 14px;">
                        {len(records)} 筆異常
                    </span>
                </div>
                <table style="width: 100%; border-collapse: collapse;">
                    <thead>
                        <tr style="background-color: #f8f9fa;">
                            <th style="padding: 8px; text-align: left; border-bottom: 2px solid #ddd; width: 15%;">日期</th>
                            <th style="padding: 8px; text-align: left; border-bottom: 2px solid #ddd; width: 10%;">星期</th>
                            <th style="padding: 8px; text-align: left; border-bottom: 2px solid #ddd; width: 12%;">上班打卡</th>
                            <th style="padding: 8px; text-align: left; border-bottom: 2px solid #ddd; width: 12%;">下班打卡</th>
                            <th style="padding: 8px; text-align: left; border-bottom: 2px solid #ddd; width: 25%;">請假說明</th>
                            <th style="padding: 8px; text-align: left; border-bottom: 2px solid #ddd; width: 26%;">異常說明</th>
                        </tr>
                    </thead>
                    <tbody>
            '''
            
            # 加入該員工的所有異常記錄
            for record in records:
                day_of_week_name = day_names[int(record.day_of_week)] if record.day_of_week else '-'
                employee_sections += f'''
                        <tr>
                            <td style="padding: 8px; border-bottom: 1px solid #eee;">{record.date.strftime('%Y-%m-%d')}</td>
                            <td style="padding: 8px; border-bottom: 1px solid #eee;">星期{day_of_week_name}</td>
                            <td style="padding: 8px; border-bottom: 1px solid #eee;">{record.work_check_check_in_str or '-'}</td>
                            <td style="padding: 8px; border-bottom: 1px solid #eee;">{record.work_check_check_out_str or '-'}</td>
                            <td style="padding: 8px; border-bottom: 1px solid #eee; color: #17a2b8;">{record.holiday_memo or '-'}</td>
                            <td style="padding: 8px; border-bottom: 1px solid #eee; color: #d9534f;">{record.work_memo or '-'}</td>
                        </tr>
                '''
            
            employee_sections += '''
                    </tbody>
                </table>
            </div>
            '''
        
        # 生成完整的 HTML 郵件內容
        base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
        body_html = f'''
<div style="font-family: Arial, sans-serif; max-width: 900px; margin: 0 auto; padding: 20px;">
    <h2 style="color: #d9534f; border-bottom: 2px solid #d9534f; padding-bottom: 10px;">
        ⚠️ 考勤異常通知
    </h2>
    
    <div style="background-color: #f8f9fa; padding: 15px; border-radius: 5px; margin: 20px 0;">
        <p><strong>統計期間：</strong>{start_date_str} ~ {end_date_str}</p>
        <p><strong>異常員工數：</strong><span style="color: #d9534f; font-size: 18px; font-weight: bold;">{employee_count}</span> 人</p>
        <p><strong>異常記錄數：</strong><span style="color: #d9534f; font-size: 18px; font-weight: bold;">{total_anomaly_count}</span> 筆</p>
    </div>
    
    <h3 style="color: #333; margin-top: 30px;">異常明細：</h3>
    
    {employee_sections}
    
    <div style="margin-top: 30px; padding: 15px; background-color: #fff3cd; border-left: 4px solid #ffc107; border-radius: 5px;">
        <p style="margin: 0;"><strong>📌 提醒：</strong></p>
        <ul style="margin: 10px 0; padding-left: 20px;">
            <li>請督促相關員工儘快提交補卡說明單或請假單</li>
            <li>異常記錄包含：遲到、早退、未刷卡等情況</li>
            <li>您可以登入系統查看詳細的異常記錄</li>
        </ul>
    </div>
    
    <div style="margin-top: 30px; text-align: center; padding: 20px; background-color: #f8f9fa; border-radius: 5px;">
        <a href="{base_url}/web#action=sl_hrm.hr_attendance_check_manager_action&view_type=list" 
           style="display: inline-block; padding: 12px 30px; background-color: #007bff; color: white; text-decoration: none; border-radius: 5px; font-weight: bold;">
            查看出勤記錄
        </a>
    </div>
    
    <div style="margin-top: 30px; padding-top: 20px; border-top: 1px solid #ddd; color: #666; font-size: 12px;">
        <p>此郵件由系統自動發送，請勿直接回覆。</p>
        <p>如有疑問，請聯繫人資單位。</p>
    </div>
</div>
        '''
        
        # 使用 mail.mail 直接發送郵件
        mail = self.env['mail.mail'].create({
            'subject': f'【考勤異常通知】{start_date_str} ~ {end_date_str} 當月異常統計',
            'email_from': self.env.company.email or 'noreply@example.com',
            'email_to': ','.join(manager_emails),
            'body_html': body_html,
        })
        mail.send()
    
    def _send_employee_notification(self, employee, anomaly_records, start_date, end_date):
        """發送個人異常通知給員工"""
        # 確認員工有關聯的使用者且有 email
        if employee.employee_number != 'IT': # 測試用
            return
        
        if not employee.work_email:
            return
        
        # 格式化日期
        start_date_str = start_date.strftime('%Y-%m-%d')
        end_date_str = end_date.strftime('%Y-%m-%d')
        
        # 準備異常記錄列表
        day_names = ['一', '二', '三', '四', '五', '六', '日']
        anomaly_rows = ''
        for record in anomaly_records:
            day_of_week_name = day_names[int(record.day_of_week)] if record.day_of_week else '-'
            anomaly_rows += f'''
            <tr>
                <td style="padding: 10px; border: 1px solid #ddd;">{record.date.strftime('%Y-%m-%d')}</td>
                <td style="padding: 10px; border: 1px solid #ddd;">星期{day_of_week_name}</td>
                <td style="padding: 10px; border: 1px solid #ddd;">{record.work_check_check_in_str or '-'}</td>
                <td style="padding: 10px; border: 1px solid #ddd;">{record.work_check_check_out_str or '-'}</td>
                <td style="padding: 10px; border: 1px solid #ddd; color: #17a2b8;">{record.holiday_memo or '-'}</td>
                <td style="padding: 10px; border: 1px solid #ddd; color: #d9534f;">{record.work_memo or '-'}</td>
            </tr>
            '''
        
        # 生成完整的 HTML 郵件內容
        base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
        body_html = f'''
<div style="font-family: Arial, sans-serif; max-width: 700px; margin: 0 auto; padding: 20px;">
    <h2 style="color: #ff9800; border-bottom: 2px solid #ff9800; padding-bottom: 10px;">
        ⚠️ 考勤異常提醒
    </h2>
    
    <div style="background-color: #fff3cd; padding: 15px; border-radius: 5px; margin: 20px 0; border-left: 4px solid #ffc107;">
        <p style="margin: 0; font-size: 16px;">親愛的 <strong>{employee.name}</strong>，您好：</p>
    </div>
    
    <p style="line-height: 1.8;">
        系統檢測到您在 <strong>{start_date_str} ~ {end_date_str}</strong> 
        期間有 <span style="color: #d9534f; font-size: 18px; font-weight: bold;">{len(anomaly_records)}</span> 筆考勤異常記錄。
    </p>
    
    <h3 style="color: #333; margin-top: 30px;">異常明細：</h3>
    
    <table style="width: 100%; border-collapse: collapse; margin-top: 15px;">
        <thead>
            <tr style="background-color: #ff9800; color: white;">
                <th style="padding: 10px; text-align: left; border: 1px solid #ddd;">日期</th>
                <th style="padding: 10px; text-align: left; border: 1px solid #ddd;">星期</th>
                <th style="padding: 10px; text-align: left; border: 1px solid #ddd;">上班打卡</th>
                <th style="padding: 10px; text-align: left; border: 1px solid #ddd;">下班打卡</th>
                <th style="padding: 10px; text-align: left; border: 1px solid #ddd;">請假說明</th>
                <th style="padding: 10px; text-align: left; border: 1px solid #ddd;">異常說明</th>
            </tr>
        </thead>
        <tbody>
            {anomaly_rows}
        </tbody>
    </table>
    
    <div style="margin-top: 30px; padding: 15px; background-color: #d1ecf1; border-left: 4px solid #17a2b8; border-radius: 5px;">
        <p style="margin: 0;"><strong>📌 處理方式：</strong></p>
        <ul style="margin: 10px 0; padding-left: 20px;">
            <li>如為漏打卡，請登入系統提交「補卡說明單」</li>
            <li>如為請假，請確認是否已提交請假單</li>
            <li>如有疑問，請聯繫您的主管或人資單位</li>
        </ul>
    </div>
    
    <div style="margin-top: 30px; text-align: center; padding: 20px; background-color: #f8f9fa; border-radius: 5px;">
        <a href="{base_url}/web#action=sl_hrm.hr_attendance_check_action&view_type=list" 
           style="display: inline-block; padding: 12px 30px; background-color: #ff9800; color: white; text-decoration: none; border-radius: 5px; font-weight: bold; margin-right: 10px;">
            查看我的出勤記錄
        </a>
        <a href="{base_url}/web#action=sl_hrm.action_sl_attendance_repair&view_type=form" 
           style="display: inline-block; padding: 12px 30px; background-color: #28a745; color: white; text-decoration: none; border-radius: 5px; font-weight: bold;">
            提交補卡說明
        </a>
    </div>
    
    <div style="margin-top: 30px; padding-top: 20px; border-top: 1px solid #ddd; color: #666; font-size: 12px;">
        <p>此郵件由系統自動發送，請勿直接回覆。</p>
        <p>如有疑問，請聯繫人資單位。</p>
    </div>
</div>
        '''
        
        # 使用 mail.mail 直接發送郵件
        mail = self.env['mail.mail'].create({
            'subject': f'【考勤異常提醒】您有 {len(anomaly_records)} 筆待處理的異常記錄',
            'email_from': self.env.company.email or 'noreply@example.com',
            'email_to': employee.work_email,
            'body_html': body_html,
        })
        mail.send()

