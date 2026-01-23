from odoo import api, fields, models
from odoo.exceptions import UserError


class StarryLordHolidayAllocation(models.Model):
    _name = 'starrylord.holiday.allocation'
    _description = '假別分配'
    _order = 'year desc, employee_number asc'

    name = fields.Char(string="名稱", related='holiday_type_id.name')
    year = fields.Char(string="年度")
    holiday_type_id = fields.Many2one("starrylord.holiday.type", string="假別")
    time_type = fields.Selection([('day', '日'), ('hour', '小時'), ('half', '半小時'), ("quarter", "十五分鐘")],
                                 related="holiday_type_id.request_unit",
                                 related_sudo=True, store=True)
    duration_min = fields.Selection(selection=[('0', '0'), ('0.5', '30')], string='分配時長(分)')
    duration_min_quarter = fields.Selection(selection=[('0', '0'), ('0.25', '15'), ('0.5', '30'), ('0.75', '45')],
                                            string='分配時長(分)')
    duration_time = fields.Integer(string='分配時長(小時)')
    duration_date = fields.Integer(string='分配時長(天)')
    employee_id = fields.Many2one(comodel_name='hr.employee.public', string='員工', required=True)
    user_id = fields.Many2one(comodel_name='res.users', string='User', related='employee_id.user_id', related_sudo=True,)
    company_id = fields.Many2one(comodel_name="res.company", string="公司別", related="employee_id.company_id",)
    validity_start = fields.Date(string='有效日期-起', required=True)
    validity_end = fields.Date(string='有效日期-迄', required=True)
    note = fields.Char(string='備註')
    distribute_time = fields.Float(string="分配時數", compute='_compute_distribute_time', store=True)
    last_time = fields.Float(string="剩餘時數", compute='compute_completed_usage')
    completed_usage = fields.Boolean(string="使用完畢", compute_sudo=True, compute='compute_completed_usage', store=False)
    used_record_ids = fields.One2many('starrylord.holiday.used.record', 'holiday_allocation_id', string='對應休假紀錄')

    # 從 sl_hrm_overtime 合併
    sl_overtime_apply_id = fields.Many2one(comodel_name='starrylord.overtime.apply', string='加班單')
    rate = fields.Float(string='加班費率')

#    employee_number = fields.Char(
#        string='員工編號',
#        related="employee_id.employee_number",
#        store=True
#    )

    employee_number = fields.Char(string='員工編號')

    is_expired = fields.Boolean(
        string='已過期',
        compute='_compute_is_expired',
        store=True,
        index=True,
        help='依有效期限自動判斷，validity_end < 今日'
    )

    # 補上過期思考
    @api.depends('validity_end')
    def _compute_is_expired(self):
        """
        判斷休假分配是否已過期
        規則：validity_end < today
        """
        today = fields.Date.today()
        for rec in self:
            if rec.validity_end:
                rec.is_expired = rec.validity_end < today
            else:
                rec.is_expired = False

    # =========================
    # Cron：每日更新過期狀態
    # =========================
    def _cron_update_expired_allocation(self):
        """
        每日由 cron 呼叫，確保 is_expired 狀態正確
        （避免 record 沒被讀取時 compute 不刷新）
        """
        today = fields.Date.today()

        # 找出「理論上已過期，但狀態尚未更新」的 allocation
        allocations = self.search([
            ('validity_end', '<', today),
            ('is_expired', '=', False),
        ])

        if allocations:
            allocations.write({'is_expired': True})

        # 同時保護性處理：若有效期限被延長，要能自動恢復為未過期
        allocations_restore = self.search([
            ('validity_end', '>=', today),
            ('is_expired', '=', True),
        ])

        if allocations_restore:
            allocations_restore.write({'is_expired': False})

    def _compute_display_name(self):
        for rec in self:
            name = rec.holiday_type_id.name
            rec.display_name = '%s - %s' % (rec.employee_id.name, name)

    @api.constrains('year')
    def check_year(self):
        for rec in self:
            try:
                check_type = int(rec.year)
            except:
                raise UserError('格式錯誤(年度請輸入西元年)')
            if check_type < 1911 or len(rec.year) != 4:
                raise UserError('年度請輸入西元年')

    @api.depends('duration_date', 'duration_time', 'duration_min', 'duration_min_quarter')
    def _compute_distribute_time(self):
        for rec in self:
            if rec.time_type == 'half':
                minute = float(rec.duration_min)
            else:
                minute = float(rec.duration_min_quarter)
            all_time = rec.duration_date * 8 + rec.duration_time + minute
            rec.distribute_time = all_time


    def compute_completed_usage(self):
        for rec in self:
            rec.completed_usage = False
            used = 0
            if rec.time_type == 'half':
                minute = float(rec.duration_min)
            else:
                minute = float(rec.duration_min_quarter)
            for tmp in rec.used_record_ids:
                used += tmp.hours
            if used >= ((rec.duration_date * 8) + (rec.duration_time) + minute):
                rec.completed_usage = True
                rec.last_time = 0
            else:
                rec.last_time = ((rec.duration_date * 8) + (rec.duration_time) + minute) - used

    def compute_last_time(self):
        used = 0
        if self.time_type == 'half':
            minute = float(self.duration_min)
        else:
            minute = float(self.duration_min_quarter)
        for tmp in self.used_record_ids:
            used += tmp.hours
        if used >= ((self.duration_date * 8) + (self.duration_time) + minute):
            last_time = 0
        else:
            last_time = ((self.duration_date * 8) + (self.duration_time) + minute) - used
        return last_time
