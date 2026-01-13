from odoo import models, fields, api, _
import datetime
import json


class HrLaborHarmInsuranceHistory(models.Model):
    _name = 'hr.labor.harm.insurance.history'
    _description = '勞工職業災害保險異動歷程'
    _order = 'start_date'

    employee_id = fields.Many2one('hr.employee', string='員工')

    start_date = fields.Date(string='生效日期', required=True)
    change_date = fields.Date(string='異動日期', default=datetime.date.today())
    change_reason_selection = fields.Selection([('add', '加保'), ('off', '退保'), ('promote', '調薪')], string='異動原因', required=True)
    insurance_gap_id = fields.Many2one('hr.labor.harm.insurance.gap', string='級距')
    insurance_salary = fields.Float(string='投保薪資', related='insurance_gap_id.insurance_salary')
    attachment_ids = fields.Many2many(comodel_name='ir.attachment', string='附件', relation="m2m_ir_labor_harm_insurance_history_rel",
                                      column1="m2m_id", column2="attachment_id",)

    @api.model_create_multi
    def create(self, vals_list):
        records = super(HrLaborHarmInsuranceHistory, self).create(vals_list)
        for rec in records:
            for attachment in rec.attachment_ids:
                attachment.sudo().public = True
        return records

    def write(self, vals):
        data = super(HrLaborHarmInsuranceHistory, self).write(vals)
        for rec in self:
            for attachment in rec.attachment_ids:
                attachment.sudo().public = True
        return data

    def unlink(self):
        for rec in self:
            for attachment in rec.attachment_ids:
                attachment.sudo().public = False
        return super(HrLaborHarmInsuranceHistory, self).unlink()
