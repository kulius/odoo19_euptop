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

    @api.model
    def create(self, vals_list):
        data = super(HrLaborPensionHistory, self).create(vals_list)
        for rec in data.attachment_ids:
            rec.sudo().public = True
        return data

    @api.model
    def write(self, vals):
        data = super(HrLaborPensionHistory, self).write(vals)
        for rec in self.attachment_ids:
            rec.sudo().public = True
        return data

    @api.model
    def unlink(self):
        for rec in self.attachment_ids:
            rec.sudo().public = False
        data = super(HrLaborPensionHistory, self).unlink()
        return data

    # 必須先退保才能再加保
    # @api.model
    # def create(self, vals):
    #     # 在此確認該筆資料是否來源於計算用暫存值，是則不進行重複加退保檢查
    #     try:
    #         in_compute = vals['compute_data']
    #         del vals['compute_data']
    #     except:
    #         in_compute = False
    #     if not in_compute:
    #         user_id = self.env.context.get('active_id')
    #         # 檢查較早的資料
    #         health_insurance_history_before = self.env['hr.health.insurance.history'].search(
    #             [('health_insurance_history_id', '=', vals['health_insurance_history_id']), ('start_date', '<=', fields.Date.today())],
    #             order='start_date desc', limit=1)
    #         # 檢查較晚的資料
    #         health_insurance_history_after = self.env['hr.health.insurance.history'].search(
    #             [('health_insurance_history_id', '=', vals['health_insurance_history_id']),
    #              ('start_date', '>=', vals['start_date'])],
    #             order="start_date desc", limit=1)
    #
    #         if (vals['change_reason_selection'] == health_insurance_history_before.change_reason_selection
    #                 or vals['change_reason_selection'] == health_insurance_history_after.change_reason_selection
    #                 or health_insurance_history_before.change_reason_selection == health_insurance_history_after.change_reason_selection):
    #             if health_insurance_history_after.change_reason_selection == 'add' or check_front.change_reason_selection == 'add':
    #                 raise UserError('請先退保再進行加保')
    #             else:
    #                 if check_after and check_front:
    #                     raise UserError('不可重複退保')
    #         check_after_day = check_after.filtered(lambda r: r.start_date == vals['start_date'])
    #         check_front_day = check_after.filtered(lambda r: r.start_date == vals['start_date'])
    #         if check_after_day or check_front_day:
    #             raise UserError('不可同日加退保')
    #     return super(HrLaborInsuranceData, self).create(vals)
