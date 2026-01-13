from odoo import models, fields, api


class StarryLordResCompany(models.Model):
    _inherit = "res.company"

    company_code = fields.Char(string="Company Code")
    company_site_line_ids = fields.One2many('sl.company.site', inverse_name='company_id')
    employee_number_prefix = fields.Char(string="員工編號前綴", default="", help="員工編號前綴")
    quotation_prefix = fields.Char(string="報價單前綴", default="", help="報價單前綴")


class StarryLordCompanySite(models.Model):
    _name = 'sl.company.site'
    _description = '工務所'

    name = fields.Char(string="名稱", required=True)
    code = fields.Char(string="代碼")
    comment = fields.Char(string='備註')
    company_id = fields.Many2one(comodel_name="res.company", string="公司別")


class StarryLordWorkLocation(models.Model):
    _inherit = 'hr.work.location'
    _rec_name = 'display_name'

    code = fields.Char(string="代碼")
    is_use_for_quotation = fields.Boolean(string="是否為報價單使用", default=False)

    def _compute_display_name(self):
        for rec in self:
            rec.display_name = '%s - %s' % (rec.company_id.name, rec.name)
