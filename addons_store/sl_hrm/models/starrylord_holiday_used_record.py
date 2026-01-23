from odoo import models, fields, api


class StarryLordHolidayUsedRecord(models.Model):
    _name = 'starrylord.holiday.used.record'
    _description = '休假使用紀錄'
    order = 'employee_number asc, holiday_day desc'

    holiday_allocation_id = fields.Many2one('starrylord.holiday.allocation', string='休假分配', required=True, ondelete='cascade')
    employee_id = fields.Many2one('hr.employee.public', related="holiday_allocation_id.employee_id", string='員工', store=True)
    company_id = fields.Many2one(comodel_name="res.company", string="公司別", related="employee_id.company_id",)
    holiday_apply_id = fields.Many2one('starrylord.holiday.apply', string='請假單', ondelete='cascade')
    holiday_day = fields.Date(string='使用日期', required=True)
    holiday_day_format = fields.Char(string='使用日期（格式化）', compute='_compute_holiday_day_str', store=True)
    hours = fields.Float(string='使用時數', required=True)
    note = fields.Char(string='備註')

    holiday_type_id = fields.Many2one(
        related='holiday_allocation_id.holiday_type_id',
        comodel_name='starrylord.holiday.type',  # 請根據你的模型名稱替換
        string='假別',
        store=True
    )

    employee_info = fields.Char(
        string='員工資訊',
        compute='_compute_employee_info',
        store=True
    )

    holiday_apply_name = fields.Char(
        string='請假單單號',
        related='holiday_apply_id.name',
        store=True,
        readonly=True
    )

    @api.depends('holiday_day')
    def _compute_holiday_day_str(self):
        for rec in self:
            if rec.holiday_day:
                rec.holiday_day_format = rec.holiday_day.strftime('%Y-%m-%d')  # 或 '%Y-%-m-%-d' for Linux
            else:
                rec.holiday_day_format = ''

    @api.depends('employee_id')
    def _compute_employee_info(self):
        for rec in self:
            rec.employee_info = f"{rec.employee_id.department_id.name}\\"
            rec.employee_info += f"{rec.employee_id.employee_number}\\"
            rec.employee_info += f"{rec.employee_id.name}"