from odoo import fields, models, api
from datetime import timedelta
from dateutil.relativedelta import relativedelta


class StarryLordHrInsuranceDoc(models.Model):
    _name = 'sl.hr.insurance.doc'
    _description = '人資資料檔案'

    name = fields.Text(string="文件描述")
    file_type = fields.Selection([('layoff', '資遣'), ('assessment', '考核')], string="類型", required=True)
    file_upload = fields.Many2many(comodel_name='ir.attachment',
                                   relation="m2m_ir_hr_insurance_rel",
                                   column1="m2m_id",
                                   column2="attachment_id",
                                   string="附件檔案")
    employee_id = fields.Many2one(comodel_name='hr.employee', string="員工")

    def create(self, vals_list):
        data = super(StarryLordHrInsuranceDoc, self).create(vals_list)
        for rec in data.file_upload:
            rec.sudo().public = True
        return data

    def write(self, vals):
        data = super(StarryLordHrInsuranceDoc, self).write(vals)
        for rec in self.file_upload:
            rec.sudo().public = True
        return data

    def unlink(self):
        for rec in self.file_upload:
            rec.sudo().public = False
        return super(StarryLordHrInsuranceDoc, self).unlink()
