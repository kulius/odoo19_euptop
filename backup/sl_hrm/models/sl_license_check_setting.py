from odoo import fields, models, api


class StarryLordHealthReportCheckSetting(models.Model):
    _name = 'sl.license.check.setting'
    _description = '教育訓練和在職回訓有效設定'
    name = fields.Char(string="簡述")
    effective_year_interval = fields.Integer(string="有效年度間隔(Y)", default=1)
    effective_hour_interval = fields.Integer(string="上課時數(H)")
    training_hours = fields.Integer(string="教育訓練時數(H)")


