import datetime
from datetime import timedelta, time, date
from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
from dateutil.relativedelta import relativedelta


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
    employee_id = fields.Many2one('hr.employee.public', string='申請人', required=True,
                                  default=lambda self: self.env.user.employee_id.id)
    user_id = fields.Many2one('res.users', string='User', related='employee_id.user_id', related_sudo=True,
                              compute_sudo=True, store=True, readonly=True)
    company_id = fields.Many2one(comodel_name="res.company", string="公司別", related="employee_id.company_id",)
    department_id = fields.Many2one('hr.department', string="部門", store=True,
                                    related="employee_id.department_id")
    substitute_id = fields.Many2one('hr.employee.public', string='代理人', required=True)

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
            for holiday_allocation in rec.used_record_ids:
                holiday_allocation.unlink()

            all_time = rec.holiday_time_total  # 請假單申請總時數
            apply_from = self.merge_day_hour_time(self.start_day, self.hour_from_m.hour, self.min_from_m.minute)
            apply_to = self.merge_day_hour_time(self.end_day, self.hour_to_m.hour, self.min_to_m.minute)
            not_completed_allocation = []
            if rec.holiday_allocation_id.is_distribute:
                not_completed_allocation = self.env['starrylord.holiday.allocation'].sudo().search(
                    [('employee_id', '=', rec.employee_id.id)]).filtered(
                    lambda
                        x: x.holiday_type_id == rec.holiday_allocation_id
                           and x.validity_start <= rec.start_day and x.validity_end >= rec.end_day and x.completed_usage is False).sorted(key=lambda x: x.validity_start)

            # 產生休假使用紀錄
            # 根據休假單的日期起迄每一天產生一筆休假使用明細
            start = apply_from
            end = apply_to
            current_datetime = start
            while current_datetime <= end:
                current_leave_hours = 0
                worktime = self.env['hr.schedule.worktime'].sudo().search(
                    [('worktime_id', '=', self.employee_id.schedule_id.id),
                     ('date_type', '=', 'schedule'),
                     ('dayofweek', '=', current_datetime.date().weekday()),
                     ])
                if worktime:
                    # 你需要將 float 時間轉換為 'HH:MM' 格式的字符串
                    am_start_time = self.convert_float_time_to_string(worktime.am_start)
                    am_end_time = self.convert_float_time_to_string(worktime.am_end)
                    pm_start_time = self.convert_float_time_to_string(worktime.pm_start)
                    pm_end_time = self.convert_float_time_to_string(worktime.pm_end)
                    # 添加上午和下午的工作時間
                    shifts = []
                    if worktime.am_start and worktime.am_end:  # 有上午班
                        shifts.append((am_start_time, am_end_time))
                    if worktime.pm_start and worktime.pm_end:  # 有下午班
                        shifts.append((pm_start_time, pm_end_time))

                    if shifts:
                        for shift in shifts:
                            work_start_str, work_end_str = shift
                            work_start = datetime.datetime.combine(current_datetime,
                                                                   datetime.datetime.strptime(work_start_str,
                                                                                              "%H:%M").time())
                            work_end = datetime.datetime.combine(current_datetime,
                                                                 datetime.datetime.strptime(work_end_str,
                                                                                            "%H:%M").time())

                            # Calculate leave hours within the work shift
                            if work_start < end < work_end:
                                current_leave_hours += (end - max(start, work_start)).seconds / 3600
                            elif work_start < start < work_end:
                                current_leave_hours += (min(end, work_end) - start).seconds / 3600
                            elif start <= work_start and work_end <= end:
                                current_leave_hours += (work_end - work_start).seconds / 3600
                                
                    allocation_index = 0
                    if rec.holiday_allocation_id.is_distribute:
                        while current_leave_hours > 0 and allocation_index < len(not_completed_allocation):
                            # if holiday_allocation.time_type == 'half':
                            #     minutes = float(holiday_allocation.duration_min) / 60
                            # else:
                            #     minutes = float(holiday_allocation.duration_min_quarter)
                            # 分配的時數
                            # allocated_hours = ((holiday_allocation.duration_date * 8) + holiday_allocation.duration_time + minutes)
                            # total_used_hours = 0  # 總使用時數
                            # for use in holiday_allocation.used_record_ids:
                            #     total_used_hours += use.hours
                            # can_use: 剩餘可使用時數
                            # can_use = allocated_hours - total_used_hours
                            holiday_allocation = not_completed_allocation[allocation_index]
                            can_use = holiday_allocation.last_time

                            if can_use >= current_leave_hours:
                                self.env['starrylord.holiday.used.record'].sudo().create({
                                    'holiday_allocation_id': holiday_allocation.id,
                                    'holiday_apply_id': rec.id,
                                    'hours': current_leave_hours,
                                    'holiday_day': current_datetime.date()
                                })
                                holiday_allocation.last_time -= current_leave_hours
                                all_time -= current_leave_hours
                                current_leave_hours = 0  # 已經請完當天了
                            else:
                                self.env['starrylord.holiday.used.record'].sudo().create({
                                    'holiday_allocation_id': holiday_allocation.id,
                                    'holiday_apply_id': rec.id,
                                    'hours': can_use,
                                    'holiday_day': current_datetime.date()
                                })
                                current_leave_hours -= can_use
                                all_time -= can_use
                                holiday_allocation.last_time = 0
                                allocation_index += 1  # 換下一筆 allocation

                current_datetime = current_datetime + timedelta(days=1)
                current_datetime = current_datetime.replace(hour=0, minute=0, second=0, microsecond=0)
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