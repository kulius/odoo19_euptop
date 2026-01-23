from odoo import api, fields, models
from odoo.exceptions import UserError


class StarryLordOvertimeType(models.Model):
    _name = 'starrylord.overtime.type'
    _description = '加班類型'

    name = fields.Char(string='加班類型名稱', required=True)

    time_type = fields.Selection(
        [("hour", "小時"), ("half", "半小時"), ("quarter", "十五分鐘")],
        string="加班最短時長", default="half", required=True
    )
    date_type = fields.Selection([('schedule', '平日'), ('holiday', '國定假日'), ('day_off', '休假日'),
                                  ('regular_holiday', '例假日')], string='加班時間點')
    eight_hours = fields.Boolean(string='時數最短以八小時計算', default=False)
    rule_ids = fields.One2many('starrylord.overtime.type.rule', 'rule_id', string='費率規則')


class StarryLordOvertimeTypeRule(models.Model):
    _name = 'starrylord.overtime.type.rule'
    _description = '加班費率規則'

    rule_id = fields.Many2one('starrylord.overtime.type', string='加班類型')
    name = fields.Char(string='名稱')
    time = fields.Integer(string='時數')
    rate = fields.Float(string='費率')
