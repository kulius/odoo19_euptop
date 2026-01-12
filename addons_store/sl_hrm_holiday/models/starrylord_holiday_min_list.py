from odoo import models, fields, api


class StarryLordHolidayMinList(models.Model):
    _name = 'starrylord.holiday.min.list'
    _description = 'Holiday Minute List'
    _order = 'minute'

    name = fields.Char(string='名稱')
    minute = fields.Integer(string='分鐘')
    is_select = fields.Boolean(string='可選擇', default=False)

    @api.onchange('name')
    def _onchange_name(self):
        if self.name:
            digits = ''.join(filter(str.isdigit, self.name))
            self.minute = int(digits) if digits.isdigit() else 0
            
    @api.constrains('minute')
    def _check_hour_range(self):
        for record in self:
            if record.minute < 0 or record.minute > 59:
                raise models.ValidationError('分鐘必須介於 0 到 59 之間')