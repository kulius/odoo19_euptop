from odoo import fields, models, api
from datetime import timedelta
from dateutil.relativedelta import relativedelta


class StarryLordHrLicenseLine(models.Model):
    _name = 'sl.hr.license.line'
    _description = '證照明細'
    _rec_name = 'display_name'

    license_check_setting_id = fields.Many2one(comodel_name='sl.license.check.setting', string="證照", required=True)
    license_type = fields.Selection([('training', '初訓'), ('retraining', '回訓')], string="類型", required=True)
    license_upload = fields.Many2many(comodel_name='ir.attachment',
                                      relation="m2m_ir_license_upload_rel",
                                      column1="m2m_id",
                                      column2="attachment_id",
                                      string="檔案")
    employee_id = fields.Many2one(comodel_name='hr.employee', string="員工", readonly=True)
    user_id = fields.Many2one(comodel_name='res.users', string="使用者", readonly=True, related="employee_id.user_id")
    effective_date_start = fields.Date(string="證照取得日")
    effective_date_end = fields.Date(string="有效日期-迄")
    comment = fields.Text(string="備註")
    display_name = fields.Char(compute='_compute_display_name', store=False)

    @api.onchange('effective_date_start', 'effective_date_end')
    def _check_effective_date(self):
        for rec in self:
            if rec.effective_date_start and rec.effective_date_end:
                # start must be before end
                if rec.effective_date_start > rec.effective_date_end:
                    raise models.ValidationError('證照取得日必須小於等於有效日期-迄')

    def _compute_display_name(self):
        for rec in self:
            rec.display_name = '%s - %s' % (rec.license_check_setting_id.name, rec.license_type)

    @api.onchange('license_check_setting_id', 'effective_date_start')
    def _onchange_license_check_setting_id(self):
        for rec in self:
            if rec.license_check_setting_id and rec.effective_date_start:
                # 根據license_check_setting_id.effective_year_interval計算有效日期-迄
                rec.effective_date_end = rec.effective_date_start + relativedelta(years=rec.license_check_setting_id.effective_year_interval) if rec.effective_date_start else False
