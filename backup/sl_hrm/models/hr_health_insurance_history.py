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

    def create(self, vals_list):
        data = super(HrHealthInsuranceHistory, self).create(vals_list)
        for rec in data.attachment_ids:
            rec.sudo().public = True
        return data

    def unlink(self):
        for rec in self.attachment_ids:
            rec.sudo().public = False
        return super(HrHealthInsuranceHistory, self).unlink()

    def write(self, vals):
        data = super(HrHealthInsuranceHistory, self).write(vals)
        for rec in self.attachment_ids:
            rec.sudo().public = True
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