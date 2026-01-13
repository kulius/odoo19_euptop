from odoo import models, fields, api, _
import datetime


class HrLaborInsuranceHistory(models.Model):
    _name = 'hr.labor.insurance.history'
    _description = '勞保異動歷程'
    _order = 'start_date'

    labor_insurance_history_id = fields.Many2one('hr.employee', string='勞保異動明細')

    start_date = fields.Date(string='生效日期', required=True)
    change_date = fields.Date(string='異動日期', default=datetime.date.today())
    change_reason_selection = fields.Selection([('add', '加保'), ('off', '退保'), ('promote', '調薪')], string='異動原因', required=True, default='add')
    labor_rate = fields.Selection([('1', '無補助'), ('0.75', '補助1/4'), ('0.5', '補助1/2'), ('0', '免繳')], string='政府補助勞保費身分別', default='1')
    labor_identity = fields.Selection([('normal', '一般勞工'), ('only_accident', '僅參加就業保險'), ('no_accident', '不參加就業保險')]
                                      , string='勞工身分', default='normal')
    labor_insurance_gap_id = fields.Many2one('hr.labor.insurance.gap', string='勞保級距')
    labor_insurance_gap = fields.Float(string='勞保級距', related='labor_insurance_gap_id.insurance_salary')
    attachment_ids = fields.Many2many(comodel_name='ir.attachment', string='附件', relation="m2m_ir_labor_insurance_history_rel",
                                      column1="m2m_id", column2="attachment_id", )

    @api.model_create_multi
    def create(self, vals_list):
        records = super(HrLaborInsuranceHistory, self).create(vals_list)
        for rec in records:
            for attachment in rec.attachment_ids:
                attachment.sudo().public = True
        return records

    def write(self, vals):
        data = super(HrLaborInsuranceHistory, self).write(vals)
        for rec in self:
            for attachment in rec.attachment_ids:
                attachment.sudo().public = True
        return data

    def unlink(self):
        for rec in self:
            for attachment in rec.attachment_ids:
                attachment.sudo().public = False
        return super(HrLaborInsuranceHistory, self).unlink()
