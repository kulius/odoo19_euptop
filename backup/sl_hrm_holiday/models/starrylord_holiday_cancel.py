from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError


class StarryLordHolidayCancel(models.Model):
    _name = 'starrylord.holiday.cancel'
    _description = '銷假調整單(由HR建立)'
    _inherit = 'mail.thread'
    _order = 'create_date desc, id desc'

    name = fields.Char(string='單號', copy=False, readonly=True)
    state = fields.Selection(
        [('draft', '草稿'),
         ('confirm', '待確認'),
         ('done', '已生效'),
         ('cancel', '作廢')],
        string='狀態',
        default='draft',
        tracking=True
    )

    holiday_apply_id = fields.Many2one(
        'starrylord.holiday.apply',
        string='原請假單',
        required=True,
        ondelete='restrict',
        tracking=True
    )
    employee_id = fields.Many2one(
        'hr.employee.public',
        string='員工',
        related='holiday_apply_id.employee_id',
        store=True,
        readonly=True
    )
    company_id = fields.Many2one(
        'res.company',
        string='公司別',
        related='holiday_apply_id.company_id',
        store=True,
        readonly=True
    )

    cancel_day = fields.Date(string='銷假日期', required=True, tracking=True)
    cancel_hours = fields.Float(string='銷假時數(小時)', required=True, tracking=True)
    reason = fields.Text(string='銷假原因', required=True)

    hr_user_id = fields.Many2one('res.users', string='建立人(HR)', default=lambda self: self.env.user, readonly=True)
    approve_user_id = fields.Many2one('res.users', string='確認人(可選)', readonly=True)

    used_record_ids = fields.One2many(
        'starrylord.holiday.used.record',
        'cancel_id',
        string='本單產生的沖銷紀錄',
        readonly=True
    )

    @api.model
    def create(self, vals):
        if not vals.get('name') and vals.get('holiday_apply_id'):
            apply = self.env['starrylord.holiday.apply'].browse(vals['holiday_apply_id'])
    
            count = self.search_count([
                ('holiday_apply_id', '=', apply.id)
            ]) + 1
    
            vals['name'] = f"{apply.name}-銷假單-{count}"
    
        return super().create(vals)

    # ====== 核心計算：可銷時數 ======
    def _get_cancelable_hours_on_day(self):
        """回傳該請假單在 cancel_day 目前尚可銷的時數（已扣除先前沖銷）。"""
        self.ensure_one()
        Used = self.env['starrylord.holiday.used.record'].sudo()

        # 同一張請假單 + 同一天：正數為使用、負數為沖銷
        domain = [
            ('holiday_apply_id', '=', self.holiday_apply_id.id),
            ('holiday_day', '=', self.cancel_day),
        ]
        recs = Used.search(domain)

        used_hours = sum(recs.mapped('hours'))  # 正負加總
        # 理論上 used_hours >= 0，若 <0 代表資料已不一致
        return used_hours

    def _validate_before_confirm(self):
        self.ensure_one()

        if not self.holiday_apply_id:
            raise ValidationError(_('請先選擇原請假單。'))

        if self.holiday_apply_id.state != 'agree':
            raise ValidationError(_('只能對「已同意(agree)」的請假單進行銷假。'))

        if not self.cancel_day:
            raise ValidationError(_('請填寫銷假日期。'))

        if self.cancel_hours <= 0:
            raise ValidationError(_('銷假時數必須大於 0。'))

        # 檢查銷假日期是否落在請假單區間內（用 start_day/end_day 粗檢）
        if self.holiday_apply_id.start_day and self.holiday_apply_id.end_day:
            if not (self.holiday_apply_id.start_day <= self.cancel_day <= self.holiday_apply_id.end_day):
                raise ValidationError(_('銷假日期必須落在原請假單起迄日期範圍內。'))

        cancelable = self._get_cancelable_hours_on_day()
        if cancelable <= 0:
            raise ValidationError(_('該日目前沒有可銷的請假時數。'))

        if self.cancel_hours > cancelable:
            raise ValidationError(_('銷假時數不可大於該日可銷時數：%.2f 小時。') % cancelable)

    # ====== 狀態流 ======
    def action_confirm(self):
        for rec in self:
            rec._validate_before_confirm()
            rec.state = 'confirm'
        return True

    def action_set_draft(self):
        for rec in self:
            if rec.state == 'done':
                raise UserError(_('已生效的銷假單不可退回草稿；如需更正請另開新單沖回。'))
            rec.state = 'draft'
        return True

    def action_void(self):
        """作廢：僅允許尚未 done 的作廢；done 後要逆轉請用新銷假單沖回。"""
        for rec in self:
            if rec.state == 'done':
                raise UserError(_('已生效的銷假單不可作廢；如需更正請另開新單沖回。'))
            rec.state = 'cancel'
        return True

    # ====== 生效：產生負數 used.record（核心） ======
    def action_done(self):
        Used = self.env['starrylord.holiday.used.record'].sudo()

        for rec in self:
            if rec.state not in ('confirm', 'draft'):
                raise UserError(_('只有「草稿/待確認」的銷假單才能生效。'))

            rec._validate_before_confirm()

            # 取該日正數使用紀錄（同一張請假單），由後往前沖銷（id desc）
            positive_recs = Used.search([
                ('holiday_apply_id', '=', rec.holiday_apply_id.id),
                ('holiday_day', '=', rec.cancel_day),
                ('hours', '>', 0),
            ], order='id desc')

            if not positive_recs:
                raise UserError(_('找不到該日的請假使用紀錄，無法銷假。'))

            remaining = rec.cancel_hours

            # 逐筆產生負數沖銷，保持 allocation 正確、報表自然正確
            for ur in positive_recs:
                if remaining <= 0:
                    break

                # 該筆可用來沖銷的上限，需扣掉「同 allocation、同 apply、同 day」已沖銷的量
                # 做法：看同 allocation/day/apply 的 hours 加總（正負），得到尚餘
                same_bucket = Used.search([
                    ('holiday_apply_id', '=', rec.holiday_apply_id.id),
                    ('holiday_day', '=', rec.cancel_day),
                    ('holiday_allocation_id', '=', ur.holiday_allocation_id.id),
                ])
                bucket_sum = sum(same_bucket.mapped('hours'))
                # bucket_sum 是該 allocation 在該日的淨使用（>=0 才合理）
                bucket_cancelable = max(bucket_sum, 0.0)

                if bucket_cancelable <= 0:
                    continue

                x = min(remaining, bucket_cancelable)

                Used.create({
                    'holiday_allocation_id': ur.holiday_allocation_id.id,
                    'holiday_apply_id': rec.holiday_apply_id.id,
                    'holiday_day': rec.cancel_day,
                    'hours': -x,
                    'note': (rec.reason or '')[:255],
                    'cancel_id': rec.id,
                })

                remaining -= x

            if remaining > 1e-6:
                # 理論上不會發生（前面已校驗 total cancelable），發生就代表資料不一致
                raise UserError(_('銷假沖銷失敗：剩餘 %.2f 小時未能匹配到使用紀錄，請檢查資料一致性。') % remaining)

            rec.approve_user_id = self.env.user.id
            rec.state = 'done'

            # ⚠️ 行事曆處理：
            # 你目前 hr_personal_calendar_id 是整段請假只建一筆。
            # 部分銷假要精準拆段很複雜，建議第二階段再做。
            # 若你想第一版只允許「整張全銷」，我可以再幫你加上全銷判斷並 unlink calendar。

        return True


class StarryLordHolidayUsedRecord(models.Model):
    _inherit = 'starrylord.holiday.used.record'

    cancel_id = fields.Many2one(
        'starrylord.holiday.cancel',
        string='銷假單',
        ondelete='set null',
        index=True
    )
    is_cancel_record = fields.Boolean(string='是否為銷假沖銷', compute='_compute_is_cancel_record', store=True)

    @api.depends('hours', 'cancel_id')
    def _compute_is_cancel_record(self):
        for rec in self:
            rec.is_cancel_record = bool(rec.cancel_id) or (rec.hours < 0)





class StarryLordHolidayCancelWizard(models.TransientModel):
    _name = 'starrylord.holiday.cancel.wizard'
    _description = '建立銷假單 Wizard'

    # ===== 基本資料（由請假單帶入） =====
    holiday_apply_id = fields.Many2one(
        'starrylord.holiday.apply',
        string='原請假單',
        required=True,
        readonly=True
    )
    employee_id = fields.Many2one(
        'hr.employee.public',
        related='holiday_apply_id.employee_id',
        store=True,
        readonly=True
    )
    start_day = fields.Date(related='holiday_apply_id.start_day', readonly=True)
    end_day = fields.Date(related='holiday_apply_id.end_day', readonly=True)
    time_type = fields.Selection(
        related='holiday_apply_id.time_type',
        readonly=True
    )
    holiday_time_total = fields.Float(
        related='holiday_apply_id.holiday_time_total',
        readonly=True,
        string='原請假總時數'
    )

    # ===== 使用者輸入 =====
    cancel_day = fields.Date(string='銷假日期', required=True)
    cancel_hours = fields.Float(string='銷假時數(小時)', required=True)
    reason = fields.Text(string='銷假原因', required=True)

    # ===== 輔助顯示（非必填，但很有用）=====
    cancelable_hours_today = fields.Float(
        string='該日可銷時數',
        compute='_compute_cancelable_hours_today',
        readonly=True
    )
    canceled_hours_total = fields.Float(
        string='已銷假總時數',
        compute='_compute_canceled_hours_total',
        readonly=True
    )

    # ===== 計算：該日尚可銷時數 =====
    @api.depends('cancel_day', 'holiday_apply_id')
    def _compute_cancelable_hours_today(self):
        Used = self.env['starrylord.holiday.used.record'].sudo()
        for rec in self:
            hours = 0.0
            if rec.cancel_day and rec.holiday_apply_id:
                recs = Used.search([
                    ('holiday_apply_id', '=', rec.holiday_apply_id.id),
                    ('holiday_day', '=', rec.cancel_day),
                ])
                hours = sum(recs.mapped('hours'))  # 正負加總
            rec.cancelable_hours_today = max(hours, 0.0)

    # ===== 計算：整張假單已銷總時數 =====
    @api.depends('holiday_apply_id')
    def _compute_canceled_hours_total(self):
        Used = self.env['starrylord.holiday.used.record'].sudo()
        for rec in self:
            total = 0.0
            if rec.holiday_apply_id:
                recs = Used.search([
                    ('holiday_apply_id', '=', rec.holiday_apply_id.id),
                    ('hours', '<', 0),
                ])
                total = abs(sum(recs.mapped('hours')))
            rec.canceled_hours_total = total

    # ===== 核心防呆：Wizard 就擋 =====
    @api.constrains('cancel_day', 'cancel_hours')
    def _check_cancel_rules(self):
        for rec in self:
            if not rec.cancel_day or not rec.holiday_apply_id:
                continue

            # --- 規則 1：必須在原請假期間 ---
            if not (rec.start_day <= rec.cancel_day <= rec.end_day):
                raise ValidationError(_('銷假日期必須在原請假期間內。'))

            # --- 基本值檢查 ---
            if rec.cancel_hours <= 0:
                raise ValidationError(_('銷假時數必須大於 0。'))

            # --- 該日可銷時數 ---
            cancelable_today = rec.cancelable_hours_today
            if cancelable_today <= 0:
                raise ValidationError(_('該日沒有可銷的請假時數。'))

            # --- 規則 2：單日最多 8 小時，且不得超過當日實際請假 ---
            daily_limit = min(8.0, cancelable_today)
            if rec.cancel_hours > daily_limit:
                raise ValidationError(
                    _('單日最多只能銷假 %.2f 小時（該日實際請假 %.2f 小時）。')
                    % (daily_limit, cancelable_today)
                )

            # --- 規則 3：累計銷假不可超過原請假 ---
            if rec.canceled_hours_total + rec.cancel_hours > rec.holiday_time_total:
                raise ValidationError(
                    _('銷假總時數不可超過原請假 %.2f 小時，目前已銷 %.2f 小時。')
                    % (rec.holiday_time_total, rec.canceled_hours_total)
                )

    # ===== 建立銷假單 =====
    def action_create_cancel(self):
        self.ensure_one()

        cancel = self.env['starrylord.holiday.cancel'].create({
            'holiday_apply_id': self.holiday_apply_id.id,
            'cancel_day': self.cancel_day,
            'cancel_hours': self.cancel_hours,
            'reason': self.reason,
        })

        return {
            'type': 'ir.actions.act_window',
            'res_model': 'starrylord.holiday.cancel',
            'res_id': cancel.id,
            'view_mode': 'form',
            'target': 'current',
        }
