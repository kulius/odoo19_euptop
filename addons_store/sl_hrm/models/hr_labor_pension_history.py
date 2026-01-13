from odoo import models, fields, api, _
import datetime


class HrLaborPensionHistory(models.Model):
    _name = 'hr.labor.pension.history'
    _description = '勞退異動歷程'
    _order = 'start_date'

    employee_id = fields.Many2one('hr.employee', string='員工')

    start_date = fields.Date(string='生效日期', required=True)
    change_date = fields.Date(string='異動日期', default=datetime.date.today())
    change_reason_selection = fields.Selection([('add', '加保'), ('off', '退保'), ('promote', '調薪'), ('self_contribution', '自提')], string='異動原因', required=True)
    self_reimbursement_of_labor_pension = fields.Selection([('0.00', '0%'),
                                                            ('0.01', '1%'),
                                                            ('0.02', '2%'),
                                                            ('0.03', '3%'),
                                                            ('0.04', '4%'),
                                                            ('0.05', '5%'),
                                                            ('0.06', '6%')], string='勞退自提比例', default='0.00')

    comp_reimbursement_of_labor_pension = fields.Selection([('0.00', '0%'),
                                                            ('0.01', '1%'),
                                                            ('0.02', '2%'),
                                                            ('0.03', '3%'),
                                                            ('0.04', '4%'),
                                                            ('0.05', '5%'),
                                                            ('0.06', '6%')], string='勞退公司提撥比例', default='0.06')

    labor_pension_gap_id = fields.Many2one('hr.labor.pension.gap', string='勞退級距')
    labor_pension_salary = fields.Float(string='勞退薪資', readonly=True, related='labor_pension_gap_id.insurance_salary')
    attachment_ids = fields.Many2many(comodel_name='ir.attachment', string='附件', relation="m2m_ir_labor_pension_insurance_history_rel",
                                      column1="m2m_id", column2="attachment_id", )

    @api.model_create_multi
    def create(self, vals_list):
        records = super(HrLaborPensionHistory, self).create(vals_list)
        for rec in records:
            for attachment in rec.attachment_ids:
                attachment.sudo().public = True
        return records

    def write(self, vals):
        data = super(HrLaborPensionHistory, self).write(vals)
        for rec in self:
            for attachment in rec.attachment_ids:
                attachment.sudo().public = True
        return data

    def unlink(self):
        for rec in self:
            for attachment in rec.attachment_ids:
                attachment.sudo().public = False
        return super(HrLaborPensionHistory, self).unlink()
