from odoo import models, fields, api, _
import datetime


class HrHealthInsuranceHistory(models.Model):
    _name = 'hr.health.insurance.history'
    _description = '健保異動歷程'
    _order = 'start_date'

    health_insurance_history_id = fields.Many2one('hr.employee', string='員工')

    start_date = fields.Date(string='生效日期', required=True)
    change_date = fields.Date(string='異動日期', default=datetime.date.today())
    change_reason_selection = fields.Selection([('add', '加保'), ('off', '退保'), ('promote', '調薪')], string='異動原因', required=True, default='add')
    health_rate = fields.Selection([('1', '無補助'), ('0.75', '補助1/4'), ('0.5', '補助1/2'), ('0', '免繳')],
                                   string='政府補助健保費身份別', default='1')
    heath_rate_type = fields.Selection(selection=[('legal', '雇主'), ('employee', '員工')], string='投保身份', default='employee')

    health_insurance_gap_id = fields.Many2one('hr.health.insurance.gap', string='健保級距')
    health_insurance_gap = fields.Float(string='投保薪資', readonly=True, related='health_insurance_gap_id.insurance_salary')
    attachment_ids = fields.Many2many(comodel_name='ir.attachment', string='附件', relation="m2m_ir_health_insurance_history_rel",
                                      column1="m2m_id", column2="attachment_id", )

    @api.model_create_multi
    def create(self, vals_list):
        records = super(HrHealthInsuranceHistory, self).create(vals_list)
        for rec in records:
            for attachment in rec.attachment_ids:
                attachment.sudo().public = True
        return records

    def unlink(self):
        for rec in self:
            for attachment in rec.attachment_ids:
                attachment.sudo().public = False
        return super(HrHealthInsuranceHistory, self).unlink()

    def write(self, vals):
        data = super(HrHealthInsuranceHistory, self).write(vals)
        for rec in self:
            for attachment in rec.attachment_ids:
                attachment.sudo().public = True
        return data
