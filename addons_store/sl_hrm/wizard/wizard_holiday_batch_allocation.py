from odoo import api, fields, models
from odoo.exceptions import UserError


class WizardHolidayBatchAllocation(models.Model):
    _name = "wizard.holiday.batch.allocation"
    _description = "休假批次分配"

    year = fields.Char(string="年度")
    holiday_type_id = fields.Many2one("starrylord.holiday.type", string="假別")
    time_type = fields.Selection([('day', '日'), ('hour', '小時'), ('half', '半小時'), ("quarter", "十五分鐘")],
                                 related="holiday_type_id.request_unit",
                                 related_sudo=True, compute_sudo=True, store=True)
    duration_min = fields.Selection(selection=[('0', '0'), ('30', '30')], string='時長(分)')
    duration_min_quarter = fields.Selection(selection=[('0', '0'), ('0.25', '15'), ('0.5', '30'), ('0.75', '45')],
                                            string='時長(分)')
    duration_time = fields.Integer(string='時長(小時)')
    duration_date = fields.Integer(string='時長(天)')
    employee_ids = fields.Many2many('hr.employee', string='員工', required=True)
    validity_start = fields.Date(string='假期開始日期', required=True)
    validity_end = fields.Date(string='假期結束日期', required=True)
    note = fields.Char(string='備註')
    distribute_time = fields.Float(string="分配時數", compute='_compute_distribute_time', store=True)

    def allocation_add(self):
        for rec in self:
            try:
                if int(rec.year) < 1911 or len(rec.year) != 4:
                    raise UserError('請輸入西元年')
            except:
                raise UserError('格式錯誤')
            if rec.time_type == 'half':
                min_type = 'duration_min'
                min_value = rec.duration_min
            else:
                min_type = 'duration_min_quarter'
                min_value = rec.duration_min_quarter
            for employee in rec.employee_ids:
                rec.env['starrylord.holiday.allocation'].create(
                    {'year': rec.year, 'holiday_type_id': rec.holiday_type_id.id,
                     'duration_time': rec.duration_time, 'duration_date': rec.duration_date, 'employee_id': employee.id,
                     'validity_start': rec.validity_start, 'validity_end': rec.validity_end, 'note': rec.note})

    @api.depends('duration_date', 'duration_time', 'duration_min', 'duration_min_quarter')
    def _compute_distribute_time(self):
        for rec in self:
            if rec.time_type == 'half':
                minute = float(rec.duration_min)
            else:
                minute = float(rec.duration_min_quarter)
            all_time = rec.duration_date * 8 + rec.duration_time + minute
            rec.distribute_time = all_time
