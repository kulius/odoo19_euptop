from datetime import time

from odoo import api, fields, models


class StarryLordHolidayPersonal(models.Model):
    _name = 'starrylord.holiday.personal'
    _description = '休假表'

    name = fields.Char(string='名稱')
    holiday_ids = fields.One2many('starrylord.holiday.personal.data', 'holiday_id')
    is_public_holiday = fields.Boolean(string='是否適用國定假日')


class StarryLordHolidayPersonalData(models.Model):
    _name = 'starrylord.holiday.personal.data'
    _description = '休假表明細'

    holiday_id = fields.Many2one('starrylord.holiday.personal', 'holiday_ids')
    name = fields.Char(string='名稱')
    holiday_type = fields.Selection([('day_off', '休假日'), ('regular_holiday', '例假日'), ('no_work', '空班')],
                                    string='休假類型')
    dayofweek = fields.Selection(
        [('0', '周一'), ('1', '周二'), ('2', '周三'), ('3', '周四'), ('4', '周五'), ('5', '周六'),
         ('6', '周日')], string='星期')
    holiday_start = fields.Float(string='開始時間')
    holiday_end = fields.Float(string='結束時間')

    @api.model
    def create(self, vals):
        if not vals['name']:
            weekStr = '周一 周二 周三 周四 周五 周六 周日 '
            time_seconds_start = int(vals['holiday_start'] * 3600)
            time_obj_start = time(hour=(time_seconds_start // 3600), minute=(time_seconds_start % 3600) // 60)
            time_seconds_end = int(vals['holiday_end'] * 3600)
            time_obj_end = time(hour=(time_seconds_end // 3600), minute=(time_seconds_end % 3600) // 60)
            weekid = int(vals['dayofweek']) * 3
            vals['name'] = weekStr[weekid: weekid + 3] + time_obj_start.strftime('%H:%M') + '-' + time_obj_end.strftime(
                '%H:%M')
        return super(StarryLordHolidayPersonalData, self).create(vals)
