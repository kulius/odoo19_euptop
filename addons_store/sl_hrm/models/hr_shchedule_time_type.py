from odoo import api, fields, models


class HrScheduleTimeType(models.Model):
    _name = 'hr.schedule.time.type'
    _description = '排班時間代號定義'

    name = fields.Char(string='代號', required=True)
    date_type = fields.Selection([('schedule', '排班'), ('overtime', '加班'), ('leave', '請假'), ('no_work', '空班'),
                                  ('holiday', '國定假日'), ('day_off', '休假日'), ('regular_holiday', '例假日')],
                                 string='類型', default='schedule')
    note = fields.Char(string='代號說明', required=False)
    work_start = fields.Float(string='開始時間')
    work_end = fields.Float(string='結束時間')
    am_start = fields.Float(string='上午開始時間')
    am_end = fields.Float(string='上午結束時間')
    pm_start = fields.Float(string='下午開始時間')
    pm_end = fields.Float(string='下午結束時間')
