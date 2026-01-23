import datetime
from datetime import timedelta, time, date
from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
from dateutil.relativedelta import relativedelta
from collections import defaultdict


class StarryLordHolidayApply(models.Model):
    _name = 'starrylord.holiday.apply'
    _inherit = 'mail.thread'
    _description = '請假申請'
    _order = 'create_date desc, id desc'
    _rec_name = 'calendar_display_name'

    holiday_allocation_id = fields.Many2one('starrylord.holiday.type', string='休假類型', store=True, readonly=False,
                                            required=True,
                                            compute='_compute_holiday_allocation_id',
                                            )
    employee_id = fields.Many2one('hr.employee', string='申請人', required=True,
                                  default=lambda self: self.env.user.employee_id.id)
    user_id = fields.Many2one('res.users', string='User', related='employee_id.user_id', related_sudo=True,
                              compute_sudo=True, store=True, readonly=True)
    company_id = fields.Many2one(comodel_name="res.company", string="公司別", related="employee_id.company_id",)
    department_id = fields.Many2one('hr.department', string="部門", store=True,
                                    related="employee_id.department_id")
    substitute_id = fields.Many2one('hr.employee', string='代理人', required=True)

    substitute_user_id = fields.Many2one('res.users', string='代理人使用者帳號', related='substitute_id.user_id', related_sudo=True,
                                         compute_sudo=True, store=True, readonly=True)
    # job_id = fields.Many2one('hr.job', string="職稱", related="employee_id.position", store=True, related_sudo=True)
    manager_id = fields.Many2one('res.users', string="管理人",
                                 related="employee_id.parent_id.user_id", store=True)
    state = fields.Selection([('draft', '草稿'),
                              ('f_approve', '待核准'),
                              ('agree', '確認執行'),
                              ('refused', '己拒絕')],
                             string="狀態",
                             default="draft")
    name = fields.Char(string='單號')
    # attendance_information = fields.Text(string='人員出缺勤參考資訊', compute='compute_information', store='True')
    attachment_ids = fields.Many2many('ir.attachment', string='附件')
    report_note = fields.Text(string='事由')
    holiday_note = fields.Text(
        string='休假備註', store=True,
        related="holiday_allocation_id.note",
    )
    # 顯示補休假分配的下拉選單，僅在選擇補休假時顯示
    holiday_allocation_id_comp = fields.Many2one(
        'starrylord.holiday.allocation',
        string='加班補休分配',
        domain=lambda self: [
            ('employee_id', '=', self.env.user.employee_id.id),
            ('holiday_type_id.name', '=', '補休假'),  # 假設補休假類型的 name 為 '補休假'
            ('validity_start', '<=', fields.Date.today()),
            ('validity_end', '>=', fields.Date.today()),
        ],
        help='僅在選擇補休假時顯示可用的補休假分配'
    )
    
    holiday_type_name = fields.Char(
        string='休假別代碼',
        related='holiday_allocation_id.name',
        store=True,
        readonly=True,
    )
    hr_personal_calendar_id = fields.Many2one('hr.personal.calendar')

    # #----------------時間處理 ----------------------
    time_type = fields.Selection([('day', '日'), ('hour', '小時'), ('half', '半小時'), ("quarter", "十五分鐘")],
                                 related="holiday_allocation_id.request_unit", store=True)

    start_day = fields.Date(string='開始日期', required=True, default=datetime.date.today())
    end_day = fields.Date(string='結束日期', required=True, default=datetime.date.today())
    hour_from_m = fields.Many2one('starrylord.holiday.hour.list', string='開始時間', domain=[('is_select', '=', True)])
    hour_to_m = fields.Many2one('starrylord.holiday.hour.list', string='結束時間', domain=[('is_select', '=', True)])
    min_from_m = fields.Many2one('starrylord.holiday.min.list', string='開始時間', domain=[('is_select', '=', True)])
    min_to_m = fields.Many2one('starrylord.holiday.min.list', string='結束時間', domain=[('is_select', '=', True)])

    apply_from = fields.Datetime(string='請假時間-起', compute='_compute_holiday_time_total', store=True)
    apply_to = fields.Datetime(string='請假時間-迄', compute='_compute_holiday_time_total', store=True)
    display_time = fields.Char(string='時長')

    # 請假總時數
    holiday_time_total = fields.Float(string='請假時數(小時)')
    used_record_ids = fields.One2many('starrylord.holiday.used.record', 'holiday_apply_id', string='對應休假分配紀錄')

    holiday_type_leave_time_total = fields.Float(string='已使用時數', compute='compute_last_time')
    last_time = fields.Float(string='剩餘可休時數', compute='compute_last_time')
    
    # 日曆視圖顯示名稱
    calendar_display_name = fields.Char(string='日曆顯示', compute='_compute_calendar_display_name')

    # 添加銷假單
    cancel_ids = fields.One2many(
        'starrylord.holiday.cancel',
        'holiday_apply_id',
        string='銷假單'
    )

    # === HR 專用：已銷假總時數（只算 done 的銷假單）===
    canceled_hours_total = fields.Float(
        string='已銷假總時數',
        compute='_compute_hr_hours',
        store=False
    )

    # === HR 專用：淨請假時數（帳務實際值）===
    net_leave_hours = fields.Float(
        string='淨請假時數',
        compute='_compute_hr_hours',
        store=False
    )

    # 20260119 添加管控流程，勾稽出勤紀錄
    # === 出勤反向檢核 ===
    leave_attendance_check_state = fields.Selection(
        [
            ('pending', '尚未檢核'),
            ('ok', '出勤正常'),
            ('ng', '出勤異常'),
        ],
        string='出勤檢核結果',
        default='pending',
        tracking=True
    )

    leave_attendance_process_state = fields.Selection(
        [
            ('no_issue', '無需處理'),
            ('pending', '待銷假'),
            ('done', '已處理'),
        ],
        string='出勤異常處理狀態',
        default='no_issue',
        tracking=True
    )

    leave_attendance_abnormal_reason = fields.Text(
        string='出勤異常說明',
        tracking=True
    )

    leave_attendance_ids = fields.Many2many(
        'hr.attendance',
        string='請假期間打卡',
        copy=False
    )

    # 20260119 檢查出勤的按鈕行為

    # === 核心：請假出勤反向檢核（以 used.record 為真相）===
    def action_check_leave_attendance(self):
        """
        請假出勤反向檢核（以 used.record 為真相）

        檢核邏輯：
        - 只檢查「帳上仍算請假」的日期
        - 僅檢查該請假日「本地日曆日內」的打卡
        """
        Attendance = self.env['hr.attendance'].sudo()
        Used = self.env['starrylord.holiday.used.record'].sudo()

        for rec in self:
            used_map = defaultdict(float)

            used_recs = Used.search([
                ('holiday_apply_id', '=', rec.id),
            ])

            for ur in used_recs:
                if ur.holiday_day:
                    used_map[ur.holiday_day] += (ur.hours or 0.0)

            abnormal_days = []
            abnormal_attendances = self.env['hr.attendance']

            for day in sorted(used_map.keys()):
                net_hours = used_map[day]
                if net_hours <= 0:
                    continue

                # === 請假日「本地日曆日」轉 UTC ===
                local_start = datetime.datetime.combine(day, time.min)
                local_end = datetime.datetime.combine(day, time.max)

                # 台灣時區 -> UTC
                day_start_utc = local_start - timedelta(hours=8)
                day_end_utc = local_end - timedelta(hours=8)

                attends = Attendance.search([
                    ('employee_id', '=', rec.employee_id.id),
                    ('check_in', '>=', day_start_utc),
                    ('check_in', '<=', day_end_utc),
                ])

                if attends:
                    abnormal_days.append(day)
                    abnormal_attendances |= attends

            if abnormal_days:
                rec.leave_attendance_check_state = 'ng'
                rec.leave_attendance_process_state = 'pending'
                rec.leave_attendance_ids = [(6, 0, abnormal_attendances.ids)]
                rec.leave_attendance_abnormal_reason = rec._build_leave_abnormal_reason(
                    abnormal_days=abnormal_days,
                    used_map=used_map,
                    abnormal_attendances=abnormal_attendances,
                )
            else:
                rec.leave_attendance_check_state = 'ok'
                rec.leave_attendance_process_state = 'no_issue'
                rec.leave_attendance_ids = [(5, 0, 0)]
                rec.leave_attendance_abnormal_reason = False

    # === 組合異常說明 ===
    def _build_leave_abnormal_reason(self, abnormal_days, used_map, abnormal_attendances):
        """
        逐日呈現請假出勤異常

        abnormal_days: list[date]，實際有打卡的請假日期
        used_map: dict {date: net_leave_hours}
        abnormal_attendances: hr.attendance recordset
        """
        lines = []
        lines.append('請假期間發現實際出勤紀錄')
        lines.append('')

        # === 將打卡依日期分組（以 check_in 為準）===
        attendance_by_day = defaultdict(list)
        for att in abnormal_attendances:
            if not att.check_in or not att.check_out:
                continue
            day = (att.check_in + timedelta(hours=8)).date()
            attendance_by_day[day].append(att)

        # === 逐日輸出（僅異常日，依日期排序）===
        for day in sorted(abnormal_days):
            net_hours = round(used_map.get(day, 0.0), 2)

            lines.append(
                f'【{day.strftime("%Y-%m-%d")}｜帳上仍算請假 {net_hours:.1f} 小時】'
            )

            day_attendances = attendance_by_day.get(day)
            if day_attendances:
                lines.append('實際打卡：')
                for att in day_attendances:
                    cin = (att.check_in + timedelta(hours=8)).strftime('%H:%M')
                    cout = (att.check_out + timedelta(hours=8)).strftime('%H:%M')
                    lines.append(f'  - {cin} ~ {cout}')
            else:
                lines.append('實際打卡：無')

            lines.append('')  # 日期區塊分隔

        return '\n'.join(lines).strip()

    # === 銷假完成後，由銷假單呼叫以標記處理完成 ===
    def action_mark_leave_attendance_done(self):
        for rec in self:
            if rec.leave_attendance_check_state != 'ng':
                continue
            rec.leave_attendance_process_state = 'done'

    # === 銷假完成後呼叫（建議在銷假單 done 時觸發）===
    def mark_leave_attendance_done(self):
        for rec in self:
            if rec.leave_attendance_check_state == 'ng':
                rec.leave_attendance_process_state = 'done'

    @api.depends(
        'cancel_ids.state',
        'cancel_ids.cancel_hours',
        'used_record_ids.hours'
    )
    def _compute_hr_hours(self):
        """
        HR 專用計算：
        - canceled_hours_total：已生效銷假(done)的總時數
        - net_leave_hours：used.record.hours 正負加總（帳務最準）
        """
        for rec in self:
            # 1. 已銷假總時數（只算 done）
            canceled = 0.0
            for cancel in rec.cancel_ids:
                if cancel.state == 'done':
                    canceled += (cancel.cancel_hours or 0.0)
            rec.canceled_hours_total = canceled

            # 2. 淨請假時數（帳務實際）
            # 正數 = 請假使用
            # 負數 = 銷假沖銷
            net = 0.0
            for ur in rec.used_record_ids:
                net += (ur.hours or 0.0)

            # 理論上不會 < 0，但保護一下
            rec.net_leave_hours = max(net, 0.0)

    # 建立銷假單行為
    def action_open_cancel_wizard(self):
        self.ensure_one()

        if self.state != 'agree':
            raise UserError(_('只有已同意的請假單才能建立銷假單。'))

        return {
            'type': 'ir.actions.act_window',
            'res_model': 'starrylord.holiday.cancel.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_holiday_apply_id': self.id,
            }
        }

    @api.depends('employee_id', 'holiday_allocation_id', 'state', 'holiday_time_total')
    def _compute_calendar_display_name(self):
        """計算日曆視圖上顯示的文字"""
        for record in self:
            state_dict = {
                'draft': '草稿',
                'f_approve': '待核准',
                'agree': '已同意',
                'refused': '已拒絕'
            }
            state_text = state_dict.get(record.state, record.state)
            
            # 格式：員工名 - 假別 (時數h) [狀態]
            display = f"{record.employee_id.name or ''} - {record.holiday_allocation_id.name or ''}"
            if record.holiday_time_total:
                display += f" ({record.holiday_time_total}h)"
            display += f" [{state_text}]"
            record.calendar_display_name = display

    # 合併輸入日期及時間
    def merge_day_hour_time(self, day, hour, minute):
        if day:
            hours = int(hour)
            minutes = int(minute)
            # Combine the date and time into a datetime
            s_datetime = datetime.datetime.combine(
                fields.Date.from_string(day),  # Convert the string date to a date object
                datetime.time(hour=hours, minute=minutes)
            )
        else:
            s_datetime = False
        return s_datetime

    @api.model
    def create(self, vals):
        # 建立單號
        vals['name'] = self.env['ir.sequence'].next_by_code('starrylord.holiday.apply.number')
        data = super(StarryLordHolidayApply, self).create(vals)
        for rec in self.attachment_ids:
            rec.sudo().public = True
        return data

    @api.model
    def write(self, vals):
        data = super().write(vals)
        for rec in self.attachment_ids:
            rec.sudo().public = True
        return data

    def unlink(self):
        for rec in self:
            if rec.state != 'draft':
                raise UserError(
                    _("您不能刪除送出的假單")
                )
        return super(StarryLordHolidayApply, self).unlink()

    def copy(self, default=None):
        for rec in self:
            if rec.state != 'draft':
                raise UserError(
                    _("您不能複製送出的假單")
                )
        return super().copy(default)

    # @api.onchange('substitute_id','hour_from_m', 'min_from_m', 'hour_to_m', 'min_to_m', 'start_day', 'end_day')
    # def _onchange_substitute_id(self):
    #     self.ensure_one()
    #     # 檢查請假日當天代理人是否同時有請假
    #     # 檢查代理人是否有請假單
    #     if self.substitute_id and (self.start_day and self.hour_from_m and self.min_from_m and self.end_day and self.hour_to_m and self.min_to_m):
    #         all_holiday = self.env['starrylord.holiday.apply'].search([('employee_id', '=', self.substitute_id.id),
    #                                                                    ('state', '!=', 'draft'),
    #                                                                    ('state', '!=', 'refused'),
    #                                                                    ('state', '!=', 'cancel')])
    #         apply_from = False
    #         apply_to = False
    #
    #         if self.start_day and self.hour_from_m and self.min_from_m:
    #             apply_from = self.merge_day_hour_time(self.start_day, self.hour_from_m.hour, self.min_from_m.minute)
    #             self.apply_from = apply_from + relativedelta(hours=-8)
    #
    #         if self.end_day and self.hour_to_m and self.min_to_m:
    #             apply_to = self.merge_day_hour_time(self.end_day, self.hour_to_m.hour, self.min_to_m.minute)
    #             self.apply_to = apply_to + relativedelta(hours=-8)
    #         now_start = apply_from
    #         now_end = apply_to
    #
    #         for holiday in all_holiday:
    #             start = holiday.apply_from + relativedelta(hours=+8)
    #             end = holiday.apply_to + relativedelta(hours=+8)
    #             if not (now_start < start and now_end <= start) and not (now_start >= end and now_end > end):
    #                 # self.agent_employee_id = False
    #                 return {
    #                     'warning': {
    #                         'title': "檢核錯誤",
    #                         'message': "代理人在本時段已經請假,不可擔任代理人",
    #                     },
    #                     'value': {
    #                         'substitute_id': None,
    #                     }
    #                 }


    @api.depends('employee_id', 'start_day')
    def _compute_holiday_allocation_id(self):
        for rec in self:
            result = {}
            docs = []
            for holiday_type in self.env['starrylord.holiday.type'].sudo().search([]):
                if not holiday_type.is_distribute:
                    docs.append(holiday_type.id)
            if rec.employee_id and rec.start_day:
                for tmp in self.env['starrylord.holiday.allocation'].sudo().search(
                        [('employee_id', '=', rec.employee_id.id), ('validity_start', '<=', rec.start_day),
                         ('validity_end', '>=', rec.start_day)]):
                    if tmp.holiday_type_id.id not in docs:
                        docs.append(tmp.holiday_type_id.id)
            docs.sort()

            # 更新holiday_allocation_id下拉選單
            if docs:
                result['domain'] = {'holiday_allocation_id': [('id', 'in', docs)]}
            else:
                result['domain'] = {'holiday_allocation_id': [('id', 'in', [])]}
            return result

    @api.onchange('substitute_id', 'hour_from_m', 'min_from_m', 'hour_to_m', 'min_to_m', 'start_day', 'end_day')
    def _compute_holiday_time_total(self):
        self.ensure_one()
        
        if not self.employee_id.schedule_id:
            raise ValidationError('查無適用班別資料,請至員工基本資料設定')

        if self.time_type == 'day' and self.start_day and self.end_day:
            # 整天的不用設定時刻，直接抓list中的最高和最低確保時間涵蓋完整
            all_hours = self.env['starrylord.holiday.hour.list'].search([], order='hour asc')
            self.hour_from_m = all_hours[0] if all_hours else False
            self.hour_to_m = all_hours[-1] if all_hours else False
            all_mins = self.env['starrylord.holiday.min.list'].search([], order='minute asc')
            self.min_from_m = all_mins[0] if all_mins else False
            self.min_to_m = all_mins[-1] if all_mins else False
        
        if not (self.start_day and self.hour_from_m and self.min_from_m and self.end_day and self.hour_to_m and self.min_to_m):
            return False
        # 重新計算請假總時數
        apply_from = False
        apply_to = False

        if self.start_day and self.hour_from_m and self.min_from_m:
            apply_from = self.merge_day_hour_time(self.start_day, self.hour_from_m.hour, self.min_from_m.minute)
            self.apply_from = apply_from + relativedelta(hours=-8)

        if self.end_day and self.hour_to_m and self.min_to_m:
            apply_to = self.merge_day_hour_time(self.end_day, self.hour_to_m.hour, self.min_to_m.minute)
            self.apply_to = apply_to + relativedelta(hours=-8)

        allocation = self.env['starrylord.holiday.allocation'].search([('employee_id', '=', self.employee_id.id),
                                                                       ('holiday_type_id', '=',
                                                                        self.holiday_allocation_id.id),
                                                                       ('validity_start', '<=', self.start_day),
                                                                       ('validity_end', '>=', self.start_day)])
        if not allocation and self.holiday_allocation_id.is_distribute:  # 需要分配的休假
            raise ValidationError('無分配%s的休假資料' % self.holiday_allocation_id.name)
        self.holiday_time_total = self.employee_id.schedule_id.calc_personal_calendar_time(self.employee_id, apply_from,
                                                                                           apply_to)

        if apply_from >= apply_to:
            self.end_day = False
            return {
                'warning': {
                    'title': "檢核錯誤",
                    'message': "開始時間，不可 等於 或 大於 結束時間",
                },
            }
        
        if self.substitute_id:
            setting = self.env['ir.config_parameter'].sudo()
            can_self_as_substitute_id = int(setting.get_param('can_self_as_substitute_id', default=0))
            if self.substitute_id == self.employee_id and not can_self_as_substitute_id:
                self.substitute_id = False
                return {
                    'warning': {
                        'title': "檢核錯誤",
                        'message': "代理人不可為自己",
                    },
                }
            all_holiday = self.env['starrylord.holiday.apply'].search([('employee_id', '=', self.substitute_id.id),
                                                                       ('state', '!=', 'draft'),
                                                                       ('state', '!=', 'refused'),
                                                                       ('state', '!=', 'cancel')])
            for holiday in all_holiday:
                # start = self.merge_day_hour_time(holiday.start_day, holiday.hour_from_m.hour, holiday.min_from_m.minute)
                # end = self.merge_day_hour_time(holiday.end_day, holiday.hour_to_m.hour, holiday.min_to_m.minute)
                start = holiday.apply_from + relativedelta(hours=+8)
                end = holiday.apply_to + relativedelta(hours=+8)
                if not (apply_from < start and apply_to <= start) and not (apply_from >= end and apply_to > end):
                    # self.agent_employee_id = False
                    self.end_day = False
                    return {
                        'warning': {
                            'title': "檢核錯誤",
                            'message': "代理人在本時段已經請假,不可擔任代理人",
                        },
                        'value': {
                            'substitute_id': None,
                        }
                    }
            
    def to_f_approve(self):
        for rec in self:
            # TODO 如果非上班日期，則不能請假
            # if rec.employee_id and rec.start_day and rec.end_day:
            #     existing_schedule = self.env['hr.personal.calendar'].search([
            #         ('employee_id', '=', rec.employee_id.id),
            #         ('start_date', '<=', rec.start_day),
            #         ('end_date', '>=', rec.end_day),
            #         ('date_type', '=', 'schedule'),
            #     ])
            #     start_day = rec.start_day.strftime("%m-%d")
            #
            #     # 如果 existing_schedule 為空值表示沒有排班
            #     if not existing_schedule:
            #         raise ValidationError(_("%s沒有排班不能請假" % start_day))

            error_msg = ''
            all_holiday = rec.env['starrylord.holiday.apply'].search([('employee_id', '=', rec.employee_id.id),
                                                                      ('state', '!=', 'draft'), ('id', '!=', rec.id),
                                                                      ('state', '!=', 'refused')])
            now_start = rec.merge_date_time(rec.start_day, float(rec.hour_from_m.hour + rec.min_from_m.minute / 60))
            now_end = rec.merge_date_time(rec.end_day, float(rec.hour_to_m.hour + rec.min_to_m.minute / 60))
            if now_end < now_start:
                raise UserError(_("開始時間不可大於結束時間"))
            for holiday in all_holiday:
                start = holiday.merge_date_time(holiday.start_day,
                                                float(holiday.hour_from_m.hour + holiday.min_from_m.minute / 60))
                end = holiday.merge_date_time(holiday.end_day,
                                              float(holiday.hour_to_m.hour + holiday.min_to_m.minute / 60))
                if start < now_end and end > now_start and rec.state != 'agree':
                    error_msg += '單號' + holiday.name + '請假單 ' + str(start) + '至' + str(end) + '請假\n'
            if error_msg:
                raise UserError('請假時間不可重複\n已於 \n' + error_msg)
            if rec.state == 'draft':
                rec.check_required()
                # rec.check_time()
                rec.create_and_check_allocation()
                setting = self.env['ir.config_parameter'].sudo()
                holiday_menstrual_id = int(setting.get_param('holiday_menstrual_id', default=False))
                # 檢查生理假
                if rec.holiday_allocation_id.id == holiday_menstrual_id:
                    all_time = 0
                    all_menstrual = self.env['starrylord.holiday.apply'].search(
                        [('employee_id', '=', self.employee_id.id),
                         ('holiday_allocation_id', '=',
                          holiday_menstrual_id),
                         ('state', '!=', 'draft')])
                    month_menstrual = all_menstrual.filtered(lambda x: x.start_day.month == self.start_day.month)
                    for menstrual in month_menstrual:
                        all_time += menstrual.holiday_time_total
                    all_time += rec.holiday_time_total
                    if all_time > 8:
                        raise UserError('生理假每月申請上限為一日')
            if rec.time_type == 'hour':
                if rec.holiday_time_total % 1 != 0:
                    raise UserError('請假總時數必須以小時為單位')
            elif rec.time_type == 'half':
                if rec.holiday_time_total % 0.5 != 0:
                    raise UserError('請假總時數必須以半小時為單位')
            elif rec.time_type == 'quarter':
                if rec.holiday_time_total % 0.25 != 0:
                    raise UserError('請假總時數必須以15分鐘為單位')
            rec.state = 'f_approve'
            # 如果沒有單號, 重新給號
            if not self.name:
                self.name = self.env['ir.sequence'].next_by_code('starrylord.holiday.apply.number')
            # if rec.hr_personal_calendar_id:
            #     rec.hr_personal_calendar_id.unlink()
            # temp 這段會因為 hr_personal_calendar_id = unknown 而出錯先卡掉

    def to_draft(self):
        for rec in self:
            rec.state = 'draft'
            used_records = self.env['starrylord.holiday.used.record'].sudo().search([
                ('holiday_apply_id', '=', rec.id)
            ])
            used_records.unlink()

    def to_refused(self):
        for rec in self:
            rec.state = 'refused'

    def agree(self):
        for rec in self:
            rec.state = 'agree'
            if rec.time_type == 'day':
                start_date = rec.start_day + relativedelta(hour=0, minute=0, second=0)
                end_date = rec.end_day + relativedelta(hour=23, minute=59, second=59)
            else:
                start_date = rec.merge_date_time(rec.start_day,
                                                 float(rec.hour_from_m.hour + rec.min_from_m.minute / 60))
                end_date = rec.merge_date_time(rec.end_day, float(rec.hour_to_m.hour + rec.min_to_m.minute / 60))
            rec.hr_personal_calendar_id = rec.env['hr.personal.calendar'].create({'employee_id': rec.employee_id.id,
                                                                                  'date_type': 'leave',
                                                                                  'calendar_date': start_date + relativedelta(hours=-8),
                                                                                  'start_date': start_date + relativedelta(hours=-8),
                                                                                  'end_date': end_date + relativedelta(hours=-8)}).id

    def manager_agree(self):
        for rec in self:
            if rec.state == 'draft':
                rec.check_required()
                rec.create_and_check_allocation()
                setting = self.env['ir.config_parameter'].sudo()
                holiday_menstrual_id = int(setting.get_param('holiday_menstrual_id', default=False))
                # 檢查生理假
                if rec.holiday_allocation_id.id == holiday_menstrual_id:
                    all_time = 0
                    all_menstrual = self.env['starrylord.holiday.apply'].search(
                        [('employee_id', '=', self.employee_id.id),
                         ('holiday_allocation_id', '=',
                          holiday_menstrual_id),
                         ('state', '!=', 'draft')])
                    month_menstrual = all_menstrual.filtered(lambda x: x.start_day.month == self.start_day.month)
                    for menstrual in month_menstrual:
                        all_time += menstrual.holiday_time_total
                    all_time += rec.holiday_time_total
                    if all_time > 8:
                        raise UserError('生理假每月申請上限為一日')
            if rec.time_type == 'hour':
                if rec.holiday_time_total % 1 != 0:
                    raise UserError('請假總時數必須以小時為單位')
            elif rec.time_type == 'half':
                if rec.holiday_time_total % 0.5 != 0:
                    raise UserError('請假總時數必須以半小時為單位')
            elif rec.time_type == 'quarter':
                if rec.holiday_time_total % 0.25 != 0:
                    raise UserError('請假總時數必須以15分鐘為單位')
            rec.state = 'agree'
            if rec.time_type == 'day':
                start_date = rec.start_day + relativedelta(hour=0, minute=0, second=0)
                end_date = rec.end_day + relativedelta(hour=23, minute=59, second=59)
            else:
                start_date = rec.merge_date_time(rec.start_day,
                                                 float(rec.hour_from_m.hour + rec.min_from_m.minute / 60))
                end_date = rec.merge_date_time(rec.end_day, float(rec.hour_to_m.hour + rec.min_to_m.minute / 60))
            rec.hr_personal_calendar_id = rec.env['hr.personal.calendar'].create({'employee_id': rec.employee_id.id,
                                                                                  'date_type': 'leave',
                                                                                  'calendar_date': start_date + relativedelta(hours=-8),
                                                                                  'start_date': start_date + relativedelta(hours=-8),
                                                                                  'end_date': end_date + relativedelta(hours=-8)}).id

    def convert_float_time_to_string(self, time_float):
        if time_float is None:
            return None
        hours = int(time_float)
        minutes = int((time_float - hours) * 60)
        return f"{hours:02d}:{minutes:02d}"

    # 將float型態的時間轉為time後合併
    def merge_date_time(self, date_field, time_field):
        # 當24至遇到24時直接加一天
        if time_field == 24:
            time_field = 0
            date_field += relativedelta(days=+1)
        # 將時間小數點轉成 time 物件
        if type(time_field) != 'time':
            time_seconds = int(time_field * 3600)
            time_obj = time(hour=(time_seconds // 3600), minute=(time_seconds % 3600) // 60,
                            second=(time_seconds % 60))
        else:
            time_obj = time_field
        # 將日期和時間合併成 datetime 物件
        datetime_obj = datetime.datetime.combine(date_field, time_obj)

        return datetime_obj

    def check_required(self):
        if self.time_type != 'day':
            if not self.hour_to_m or not self.hour_from_m or not self.min_to_m or not self.min_from_m:
                raise ValidationError('請填入完整時間')

    def create_and_check_allocation(self):
        for rec in self:
            # 先清掉舊的使用紀錄
            rec.used_record_ids.unlink()

            all_time = rec.holiday_time_total
            apply_from = rec.merge_day_hour_time(rec.start_day, rec.hour_from_m.hour, rec.min_from_m.minute)
            apply_to = rec.merge_day_hour_time(rec.end_day, rec.hour_to_m.hour, rec.min_to_m.minute)

            not_completed_allocation = []
            if rec.holiday_allocation_id.is_distribute:
                not_completed_allocation = self.env['starrylord.holiday.allocation'].sudo().search(
                    [('employee_id', '=', rec.employee_id.id)]
                ).filtered(
                    lambda x: x.holiday_type_id == rec.holiday_allocation_id
                    and x.validity_start <= rec.start_day
                    and x.validity_end >= rec.end_day
                    and not x.completed_usage
                ).sorted(key=lambda x: x.validity_start)

            current_datetime = apply_from

            while current_datetime <= apply_to:
                # === 新增：統一用行事曆判斷是否為工作日（含國定假日） ===
                day_start = current_datetime.replace(hour=0, minute=0, second=0, microsecond=0)
                day_end = day_start + timedelta(days=1)

                day_work_hours = rec.employee_id.schedule_id.calc_personal_calendar_time(
                    rec.employee_id, day_start, day_end
                )

                # 非工作日（國定假日 / 停班 / 未排班）-> 不扣假
                if day_work_hours <= 0:
                    current_datetime = day_end
                    continue

                # === 以下維持原本的逐日扣假邏輯 ===
                current_leave_hours = 0

                worktime = self.env['hr.schedule.worktime'].sudo().search([
                    ('worktime_id', '=', rec.employee_id.schedule_id.id),
                    ('date_type', '=', 'schedule'),
                    ('dayofweek', '=', current_datetime.date().weekday()),
                ])

                if worktime:
                    shifts = []
                    if worktime.am_start and worktime.am_end:
                        shifts.append((
                            rec.convert_float_time_to_string(worktime.am_start),
                            rec.convert_float_time_to_string(worktime.am_end)
                        ))
                    if worktime.pm_start and worktime.pm_end:
                        shifts.append((
                            rec.convert_float_time_to_string(worktime.pm_start),
                            rec.convert_float_time_to_string(worktime.pm_end)
                        ))

                    for start_str, end_str in shifts:
                        work_start = datetime.datetime.combine(
                            current_datetime.date(),
                            datetime.datetime.strptime(start_str, "%H:%M").time()
                        )
                        work_end = datetime.datetime.combine(
                            current_datetime.date(),
                            datetime.datetime.strptime(end_str, "%H:%M").time()
                        )

                        if work_start < apply_to < work_end:
                            current_leave_hours += (apply_to - max(apply_from, work_start)).seconds / 3600
                        elif work_start < apply_from < work_end:
                            current_leave_hours += (min(apply_to, work_end) - apply_from).seconds / 3600
                        elif apply_from <= work_start and work_end <= apply_to:
                            current_leave_hours += (work_end - work_start).seconds / 3600

                allocation_index = 0
                while current_leave_hours > 0 and allocation_index < len(not_completed_allocation):
                    allocation = not_completed_allocation[allocation_index]
                    can_use = allocation.last_time

                    if can_use >= current_leave_hours:
                        self.env['starrylord.holiday.used.record'].sudo().create({
                            'holiday_allocation_id': allocation.id,
                            'holiday_apply_id': rec.id,
                            'hours': current_leave_hours,
                            'holiday_day': current_datetime.date(),
                        })
                        allocation.last_time -= current_leave_hours
                        all_time -= current_leave_hours
                        current_leave_hours = 0
                    else:
                        self.env['starrylord.holiday.used.record'].sudo().create({
                            'holiday_allocation_id': allocation.id,
                            'holiday_apply_id': rec.id,
                            'hours': can_use,
                            'holiday_day': current_datetime.date(),
                        })
                        allocation.last_time = 0
                        current_leave_hours -= can_use
                        all_time -= can_use
                        allocation_index += 1

                current_datetime = day_end

            if rec.holiday_allocation_id.is_distribute and all_time > 0:
                raise UserError('該休假類型剩餘時數不足')

    @api.depends('employee_id', 'start_day', 'holiday_allocation_id', 'holiday_time_total')
    def compute_last_time(self):
        self.holiday_type_leave_time_total = self.holiday_time_total
        if self.employee_id and self.start_day and self.holiday_allocation_id:
            allocation_time = 0
            use_time = 0
            minute = 0
            # 分配的假別
            all_allocation = self.env['starrylord.holiday.allocation'].sudo().search(
                [('employee_id', '=', self.employee_id.id),
                 ('holiday_type_id', '=', self.holiday_allocation_id.id),
                 ('validity_start', '<=', self.start_day),
                 ('validity_end', '>=', self.start_day)])
            total_last_time = sum(all_allocation.mapped('last_time'))
            self.last_time = total_last_time
        else:
            self.last_time = 0

    @api.model
    def retrieve_dashboard(self):
        """ This function returns the values to populate the custom dashboard in
            the purchase order views.
        """
        self.check_access_rights('read')

        result = {
            'sick_leave_hours': 0,
            'annual_leave_hours': 0,
            'compensation_leave_hours': 0,
        }
        #
        # one_week_ago = fields.Datetime.to_string(fields.Datetime.now() - relativedelta(days=7))
        #
        # query = """SELECT COUNT(1)
        #                FROM mail_message m
        #                JOIN purchase_order po ON (po.id = m.res_id)
        #                WHERE m.create_date >= %s
        #                  AND m.model = 'purchase.order'
        #                  AND m.message_type = 'notification'
        #                  AND m.subtype_id = %s
        #                  AND po.company_id = %s;
        #             """
        #
        # self.env.cr.execute(query, (one_week_ago, self.env.ref('purchase.mt_rfq_sent').id, self.env.company.id))
        # res = self.env.cr.fetchone()
        # result['all_sent_rfqs'] = res[0] or 0
        #
        # # easy counts

        params = self.env['ir.config_parameter']
        holiday_special_id = params.sudo().get_param('sl_hrm_holiday.holiday_special_id', default=False)
        holiday_sick_id = params.sudo().get_param('sl_hrm_holiday.holiday_sick_id', default=False)
        holiday_leave_id = params.sudo().get_param('sl_hrm_holiday.holiday_leave_id', default=False)
        holiday_menstrual_id = params.sudo().get_param('sl_hrm_holiday.holiday_menstrual_id', default=False)
        holiday_comp_id = params.sudo().get_param('sl_hrm_holiday.holiday_comp_id', default=False)
        holiday_allocation = self.env['starrylord.holiday.allocation']
        today_date = fields.Date.today()
        my_allocation = holiday_allocation.search([('employee_id', '=', self.env.user.employee_id.id),
                                                   # ('holiday_type_id', '=', int(holiday_special_id)),
                                                   ('validity_start', '<=', today_date),
                                                   ('validity_end', '>=', today_date)], )
        annual_allocation = my_allocation.filtered(lambda x: x.holiday_type_id.id == int(holiday_special_id))
        sick_allocation = my_allocation.filtered(lambda x: x.holiday_type_id.id == int(holiday_sick_id))
        compensation_allocation = my_allocation.filtered(lambda x: x.holiday_type_id.id == int(holiday_comp_id))
        private_allocation = my_allocation.filtered(lambda x: x.holiday_type_id.id == int(holiday_leave_id))
        menstrual_allocation = my_allocation.filtered(lambda x: x.holiday_type_id.id == int(holiday_menstrual_id))
        result['annual_leave_hours'] = sum(annual_allocation.mapped('last_time'))
        result['sick_leave_hours'] = sum(sick_allocation.mapped('last_time'))
        result['compensation_leave_hours'] = sum(compensation_allocation.mapped('last_time'))
        result['private_leave_hours'] = sum(private_allocation.mapped('last_time'))
        result['menstrual_leave_hours'] = sum(menstrual_allocation.mapped('last_time'))
        result['gender'] = self.env.user.employee_id.gender
        return result
        
    def get_access_url(self):
        return f"/web#id={self.id}&model={self._name}&view_type=form"