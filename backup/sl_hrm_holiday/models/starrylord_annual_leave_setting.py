from odoo import models, fields


class StarryLordAnnualLeaveSetting(models.Model):
    _name = 'starrylord.annual.leave.setting'
    _description = '年假設定'

    seniority = fields.Float(string='服務年資(滿)')
    days = fields.Integer(string='特休天數')
    annual_period = fields.Integer(string='假期期限(月)')
