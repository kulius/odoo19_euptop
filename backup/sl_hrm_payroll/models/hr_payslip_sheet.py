from dateutil.relativedelta import relativedelta
from datetime import date, datetime, time, timedelta
from odoo import api, fields, models, _
import math
import time

from odoo.exceptions import UserError


class StarryLordPayslipSheet(models.Model):
    _name = "sl.hr.payslip.sheet"
    _description = '薪資單總表'
    _order = 'date_from desc'
    # name的預設值為y-m
    name = fields.Char(string='薪資單-標題', compute='compute_salary_date', readonly=False, store=True)
    company_id = fields.Many2one(comodel_name='res.company', string='公司', default=lambda self: self.env.company)
    salary_date = fields.Date(string='薪資月份', required=True, default=lambda self: fields.Date.today().replace(day=1) + relativedelta(months=-1))
    pay_date = fields.Date(string='發放日期', required=True, default=fields.Date.today().replace(day=5))
    actual_total_amount = fields.Float(string='實發總金額', compute="_compute_actual_total_amount")
    over_tax_amount = fields.Float(string='扣繳5%薪資金額',
                                   default=lambda self: self.env['ir.config_parameter'].sudo().get_param('sl_hrm_payroll.tax_baseline_amount', default=0))
    employee_ids = fields.Many2many(
        comodel_name="hr.employee", relation="hr_employee_payslip_batch_processing", column1="payslip_sheet_id",
        column2="employee_id",
        context={'active_test': False},
        stirng="選擇員工"
    )

    # included_employee_ids = fields.Many2many(comodel_name="hr.employee", relation="payslip_employee_rel", compute="_compute_payslip_employee_ids",)

    # 薪資起迄日期
    date_from = fields.Date(string='薪資起算日', required=True, default=lambda self: fields.Date.today().replace(day=1) + relativedelta(months=-1))
    date_to = fields.Date(string='薪資結算日', required=True, default=lambda self: fields.Date.today().replace(day=1) + relativedelta(day=1, days=-1))
    attendance_date_from = fields.Date(
        string="考勤起算日",
        default=lambda self: fields.Date.today().replace(day=1) + relativedelta(months=-1))
    attendance_date_to = fields.Date(
        string="考勤結算日",
        default=lambda self: fields.Date.today().replace(day=1) + relativedelta(day=1, days=-1))
    payslip_ids = fields.One2many(comodel_name='hr.payslip', inverse_name='sl_hr_payslip_sheet_id', string='薪資單')

    state = fields.Selection([
        ('draft', '草稿'),
        ('confirm', '已支付'),
        ('cancel', '取消'),
    ], default='draft', string='狀態')

    # @api.depends('date_from', 'date_to')
    # def _compute_payslip_employee_ids(self):
    #     for rec in self:
    #         filtered_employee_ids = self.env['hr.employee'].with_context(active_test=False).search([]).filtered(lambda employee: employee.state == 'working'
    #                                                                                              or (employee.state == 'resign' and employee.resignation_date >= rec.date_from and employee.resignation_date <= rec.date_to and employee.resignation_date is not False))
    #         rec.included_employee_ids = filtered_employee_ids

    is_salary_sheet = fields.Boolean(string='是否為薪資單', default=True, help="是否為薪資單，若為假則為獎金單")

    def action_send_payroll_mail_bath(self):
        for rec in self.payslip_ids:
            rec.send_mail_report()

    def action_generate_pdf_bath(self):
        for rec in self.payslip_ids:
            rec.action_generate_pdf()


    def action_payslip_sheet_draft(self):
        self.state = "draft"
        self.payslip_ids.write({'state': 'draft'})

    def action_payslip_sheet_done(self):
        self.state = "confirm"
        self.payslip_ids.write({'state': 'confirm'})

    def action_payslip_sheet_cancel(self):
        self.state = "cancel"

    def unlink(self):
        if any(self.payslip_ids.filtered(lambda payslip: payslip.state not in ("draft", "cancel"))):
            raise UserError(_("您不能刪除狀態為已確認的薪資單"))
        return super(StarryLordPayslipSheet, self).unlink()

    @api.depends('name', 'salary_date')
    def compute_salary_date(self):
        for rec in self:
            rec.name = rec.salary_date.strftime('%Y-%m')

    @api.onchange('salary_date')
    def onchange_salary_date(self):
        if self.salary_date:
            # 自動帶入薪資計算起迄第一天跟最後一天
            self.date_from = self.salary_date.replace(day=1)
            self.date_to = self.salary_date.replace(day=1) + relativedelta(months=1, days=-1)

    def _compute_actual_total_amount(self):
        for rec in self:
            rec.actual_total_amount = sum(rec.payslip_ids.mapped('all_subtotal'))

    def compute_payslip(self):
        self.ensure_one()
        err_msg = ''
        if not self.employee_ids:
            self.employee_ids = self.env['hr.employee'].search([
                ('company_id', '=', self.company_id.id),
                ('registration_date', '<=', self.date_to),
                '|',
                ('resignation_date', '=', False),
                ('resignation_date', '>=', self.date_from),
            ])
        for employee_id in self.employee_ids:
            if employee_id.id in self.payslip_ids.mapped('employee_id.id'):
                continue
            if not employee_id.payroll_structure_id:
                err_msg += '%s 沒有設定薪資結構\n' % employee_id.name
                continue
            payslip = self.payslip_ids.create({
                'employee_id': employee_id.id,
                'sl_hr_payslip_sheet_id': self.id,
                'date_from': self.date_from,
                'date_to': self.date_to,
                'salary_date': self.salary_date,
                'actual_pay_day': self.pay_date,
                'over_tax_amount': self.over_tax_amount,
                'payroll_structure_id': employee_id.payroll_structure_id.id,
                'attendance_date_from': self.date_from,
                'attendance_date_to': self.date_to,
            })

            payslip.compute_sheet(payslip)

        if err_msg:
            raise UserError(err_msg)
        self.payroll_adjustment()

    def transfer_to_accounting(self):
        self.ensure_one()
        if self.state not in ['confirm']:
            raise UserError(_("薪資單狀態尚未確認"))

        sl_account_move_item_line_ids = [(0, 0, {
            'name': '薪資-%s' % self.name,  # 項目
            'specification': '發放日:%s' % self.salary_date,  # 規格
            'quantity': 1,  # 數量
            'unit_price': self.actual_total_amount,  # 單價
            'unit': '批',
            'memo': '',  # 備註
        })]
        action = self.env.ref('sl_account.action_sl_account_move_sp_manager').read()[0]
        # view_mode = 'form'
        action['view_mode'] = 'form'
        # 確保 views 屬性包含 form 視圖
        action['views'] = [(self.env.ref('sl_account.view_form_sl_account_move_manager').id, 'form')]
        action['name'] = '傳票作業(含特殊)'
        # 帶入預設值
        action['context'] = {
            'default_is_transfer_to_sp': True,
            # 'default_sl_purchase_order_id': self.id,
            'default_account_type': 'expense',
            'default_move_type': 'expense',
            'default_account_account': self.env['sl.account.account'].search([('code', '=', '5110')], limit=1).id,
            'default_invoice_description': '薪資(含獎金)-%s' % self.name,
            # 'default_partner_id': self.partner_id,
            # 'default_partner_name': self.other_partner_name,
            # 'default_project_id': self.sl_purchase_request_id.sl_quotation_id.project_name,
            'default_invoice_date': self.pay_date,
            'default_due_date': self.pay_date,
            'default_payment_type_id': 'transfer',
            'default_certificate_type_id': 'none',
            'default_sl_account_move_item_line_ids': sl_account_move_item_line_ids,
            # 'default_attachment_ids': [(4, att.id) for att in self.attachment_ids],
        }
        return action

        # return {
        #     'name': '傳票作業(含特殊)',
        #     'type': 'ir.actions.act_window',
        #     'res_model': 'sl.account.move',
        #     'view_ids': [(5, 0, 0),
        #                  (0, 0, {'view_mode': 'tree', 'view_id': 'sl_account.view_tree_sl_account_move'}),
        #                  (0, 0, {'view_mode': 'kanban', 'view_id': 'sl_account.view_kanban_sl_account_move'}),
        #                  (0, 0, {'view_mode': 'form', 'view_id': 'sl_account.view_form_sl_account_move_manager'})],
        #     'view_mode': 'form',
        #     'context': {
        #         'default_is_transfer_to_sp': True,
        #         # 'default_sl_purchase_order_id': self.id,
        #         'default_account_type': 'expense',
        #         'default_move_type': 'expense',
        #         # 'default_partner_id': self.partner_id,
        #         # 'default_partner_name': self.other_partner_name,
        #         # 'default_project_id': self.sl_purchase_request_id.sl_quotation_id.project_name,
        #         # 'default_sl_quotation_id': self.sl_purchase_request_id.sl_quotation_id.id,
        #         'default_due_date': fields.Date.today(),
        #         'default_payment_type_id': 'transfer',
        #         'default_certificate_type_id': 'none',
        #         'default_sl_account_move_item_line_ids': sl_account_move_item_line_ids,
        #         # 'default_attachment_ids': [(4, att.id) for att in self.attachment_ids],
        #     },
        # }
