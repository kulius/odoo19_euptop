from odoo import models, fields, api


class StarryLordHolidayHourList(models.Model):
    _name = 'starrylord.holiday.hour.list'
    _description = 'Holiday Hour List'
    _order = 'hour'

    name = fields.Char(string='名稱')
    hour = fields.Integer(string='小時', required=True)
    is_select = fields.Boolean(string='可選擇', default=False)

    _hour_unique = models.Constraint(
        'unique(hour)',
        '小時必須是唯一的',
    )

    @api.constrains('hour')
    def _check_hour_range(self):
        for record in self:
            if record.hour < 0 or record.hour > 23:
                raise models.ValidationError('小時必須介於 0 到 23 之間')
