from odoo import models, fields, api, _
import datetime

from odoo.tools import json


class HrLaborInsuranceHistory(models.Model):
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

    @api.model
    def create(self, vals_list):
        data = super(HrLaborInsuranceHistory, self).create(vals_list)
        for rec in data.attachment_ids:
            rec.sudo().public = True
        return data

    @api.model
    def write(self, vals):
        data = super(HrLaborInsuranceHistory, self).write(vals)
        for rec in self.attachment_ids:
            rec.sudo().public = True
        return data

    @api.model
    def unlink(self):
        for rec in self.attachment_ids:
            rec.sudo().public = False
        return super(HrLaborInsuranceHistory, self).unlink()

    # @api.onchange('start_date')
    # def _compute_selectable_insurance_gap(self):
    #     self.ensure_one()
    #     result = {}
    #     docs = []
    #     for gap in self.env['hr.labor.harm.insurance.gap'].sudo().search(
    #             [('year', '=', self.start_date.strftime("%Y"))]):
    #         docs.append(gap.id)
    #
    #     docs.sort()
    #     # 更新下拉選單
    #     result['domain'] = {'insurance_gap_id': [('id', 'in', docs)]}
    #     return result


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
    #         # 檢查較早的資料
    #         check_after = self.env['hr.labor.insurance.data'].search([('labor_insurance_data_id', '=', vals['labor_insurance_data_id']),
    #                                                                  ('start_date', '<=', vals['start_date'])],
    #                                                                  order="start_date desc", limit=1)
    #         # 檢查較晚的資料
    #         check_front = self.env['hr.labor.insurance.data'].search([('labor_insurance_data_id', '=', vals['labor_insurance_data_id']),
    #                                                                  ('start_date', '>=', vals['start_date'])],
    #                                                                  order="start_date desc", limit=1)
    #         if vals['change_reason_selection'] == check_after.change_reason_selection or vals['change_reason_selection'] == check_front.change_reason_selection or check_after.change_reason_selection == check_front.change_reason_selection:
    #             if check_after.change_reason_selection == 'add' or check_front.change_reason_selection == 'add':
    #                 raise UserError('請先退保再進行加保')
    #             else:
    #                 if check_after and check_front:
    #                     raise UserError('不可重複退保')
    #         check_after_day = check_after.filtered(lambda r: r.start_date == vals['start_date'])
    #         check_front_day = check_after.filtered(lambda r: r.start_date == vals['start_date'])
    #         if check_after_day or check_front_day:
    #             raise UserError('不可同日加退保')
    #     return super(HrLaborInsuranceData, self).create(vals)