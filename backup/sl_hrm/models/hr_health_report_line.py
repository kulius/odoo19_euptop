from odoo import fields, models, api
from datetime import timedelta
from dateutil.relativedelta import relativedelta


class StarryLordHealthReportLine(models.Model):
    _name = 'sl.health.report.line'
    _description = '健康報告明細'

    name = fields.Char(string="健康報告簡述")
    health_report_upload = fields.Many2many(comodel_name='ir.attachment',
                                            relation="m2m_ir_health_report_upload_rel",
                                            column1="m2m_id",
                                            column2="attachment_id",
                                            string="報告檔案")
    employee_id = fields.Many2one(comodel_name='hr.employee', string="員工", readonly=True)

    effective_date_start = fields.Date(string="檢查日期")
    effective_date_end = fields.Date(string="報告到期日")


    @api.onchange('effective_date_start')
    def _compute_effective_date(self):
        for rec in self:
            #  計算出體檢報告檢查日期有效期限
            if rec.effective_date_start and rec.employee_id.birthday:
                # 計算檢查當下的年齡
                age = rec.effective_date_start.year - rec.employee_id.birthday.year
                # search sl_health_report_check_setting that age between age_start and age_end
                check_setting = self.env['sl.health.report.check.setting'].search([
                    ('age_start', '<=', age),
                    ('age_end', '>=', age),
                ])
                if check_setting:
                    #  set effective_date_end = effective_date_start + year_interval
                    rec.effective_date_end = rec.effective_date_start + relativedelta(years=check_setting.effective_year_interval)



