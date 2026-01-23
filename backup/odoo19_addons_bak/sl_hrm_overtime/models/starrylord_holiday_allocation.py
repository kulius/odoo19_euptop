from odoo import models, fields


class StarryLordHolidayUsedRecordInherit(models.Model):
    _inherit = 'starrylord.holiday.allocation'

    sl_overtime_apply_id = fields.Many2one(comodel_name='starrylord.overtime.apply', string='加班單')
    rate = fields.Float(string='加班費率')