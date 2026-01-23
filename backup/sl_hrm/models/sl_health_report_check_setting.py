from odoo import fields, models, api


class StarryLordHealthReportCheckSetting(models.Model):
    _name = 'sl.health.report.check.setting'
    _description = '體檢報告有效設定'
    name = fields.Char(string="健康報告簡述")
    age_start = fields.Integer(string="年齡-起", required=True)
    age_end = fields.Integer(string="年齡-迄", required=True)

    effective_year_interval = fields.Integer(string="檢查年度間隔", default=1)
