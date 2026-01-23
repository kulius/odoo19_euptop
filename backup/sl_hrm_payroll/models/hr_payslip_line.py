# Part of Odoo. See LICENSE file for full copyright and licensing details.
import datetime
from odoo import _, api, fields, models
from odoo.exceptions import UserError
from dateutil.relativedelta import relativedelta
from .hr_payslip import BrowsableObject

class HrPayslipLine(models.Model):
    _name = "hr.payslip.line"
    _description = "薪資項目"
    _order = "sequence asc"

    payslip_id = fields.Many2one(
        "hr.payslip", string="薪資單", required=True, ondelete="cascade"
    )

    second_health_payslip_id = fields.Many2one('hr.payslip')

    date_from = fields.Date("薪資起算日", related="payslip_id.date_from", store=True)
    employee_id = fields.Many2one("hr.employee", string="員工", related="payslip_id.employee_id", store=True)
    department_id = fields.Many2one(
        "hr.department", string="部門", related="employee_id.department_id", store=True
    )
    salary_rule_id = fields.Many2one("hr.salary.rule", string="規則", required=True)
    rate = fields.Float(string="比率(%)", digits="Payroll Rate", default=100.0)
    amount = fields.Integer(digits="Payroll", string='金額')
    quantity = fields.Float(digits="Payroll", default=1.0)
    total = fields.Float(

        string="合計",
        digits="Payroll",
        store=True,
    )

    infrequent = fields.Boolean(string='非經常性薪資', default=False)
    # slip_state = fields.Selection(related='slip_id.state')
    # 原繼承於hr_salary_rule
    category_id = fields.Many2one(
        "hr.salary.rule.category", string="類別", required=True
    )
    sequence = fields.Integer(
        required=True, related='salary_rule_id.sequence', store=True, help="使用預定的序列排列", string='序列'
    )
    name = fields.Char(string='名稱', related='salary_rule_id.name', store=True)
    source = fields.Char(string='來源', compute='compute_source', store=True, readonly=False)
    code = fields.Char(
        required=True,
        help="薪資規則的代碼可以被其他規則的計算公式使用。這樣的話，它是區分大小寫的。",
        string='代碼',
        related='salary_rule_id.code',
    )

    payslip_employee_setting_id = fields.Many2one("starrylord.employee.payslip.setting")
    is_employee_setting = fields.Boolean(compute="check_employee_setting")
    note = fields.Char(string="備註", store=True)
    manual = fields.Boolean(
        string="手動調整", default=False
    )

    # is_inherit_setting = fields.Boolean(string='禁用每月沿用按鈕', related="salary_rule_id.is_inherit_setting")

    @api.constrains('amount')
    def check_amount(self):
        for rec in self:
            if rec.amount < 0:
                raise UserError('不可輸入負數')

    @api.onchange('salary_rule_id')
    def onchange_salary_rule_id(self):
        self.ensure_one()
        self.sequence = self.salary_rule_id.sequence
        self.category_id = self.salary_rule_id.category_id


    # @api.depends('amount')
    # def compute_source(self):
    #     for rec in self:
    #         rec.source = ''
    #         date_from = rec.slip_id.date_from
    #         date_to = rec.slip_id.date_to
    #         if rec.code == 'Labor':
    #             labor_data = rec.employee_id.labor_insurance_data_ids.sorted('start_date', reverse=False)
    #             labor_data = labor_data.filtered(lambda x: date_to >= x.start_date >= date_from).sorted('start_date', reverse=False)
    #             if len(labor_data) > 1:
    #                 labor_data = labor_data[len(labor_data) - 1]
    #             if labor_data:
    #                 if labor_data.labor_insurance_id.insured_grade_distance > 0:
    #                     rec.source = '勞保保額 ' + datetime.datetime.strftime(labor_data.start_date + relativedelta(hours=+8), '%Y-%m-%d ') + \
    #                                  str(labor_data.labor_insurance_id.insured_grade_distance)
    #         elif rec.code == 'Healthy':
    #             health_data = rec.employee_id.health_insurance_data_ids.sorted('start_date', reverse=False)
    #             health_data = health_data.filtered(lambda x: date_to >= x.start_date >= date_from).sorted('start_date', reverse=False)
    #             if len(health_data) > 1:
    #                 health_data = health_data[len(health_data) - 1]
    #             if health_data:
    #                 if health_data.health_insurance_id.insured_grade_distance > 0:
    #                     rec.source = '健保保額 ' + datetime.datetime.strftime(health_data.start_date + relativedelta(hours=+8), '%Y-%m-%d ') + \
    #                                  str(health_data.health_insurance_id.insured_grade_distance)
    #         else:
    #             payslip_setting = rec.employee_id.alltop_payslip_employee_setting_ids.filtered(lambda x: date_to >= x.start_date and
    #                               x.salary_rule_id.id == rec.salary_rule_id.id).sorted('start_date', reverse=False)
    #             if len(payslip_setting) > 1:
    #                 payslip_setting = payslip_setting[len(payslip_setting) - 1]
    #             if payslip_setting:
    #                 if payslip_setting.amount > 0:
    #                     rec.source = payslip_setting.salary_rule_id.name + ' ' + datetime.datetime.strftime(payslip_setting.start_date
    #                                  + relativedelta(hours=+8), '%Y-%m-%d ') + str(payslip_setting.amount)

    # def add_employee_setting(self):
    #     if self.payslip_employee_setting_id:
    #         self.payslip_employee_setting_id.amount = self.amount
    #     else:
    #         setting_id = self.env['alltop.payslip.employee.setting'].create({'start_date': self.date_from,
    #                                                                          'employee_id': self.employee_id.id,
    #                                                                          'amount': self.amount,
    #                                                                         'salary_rule_id': self.salary_rule_id.id}).id
    #         self.payslip_employee_setting_id = setting_id

    def open_edit_dialog(self):
        """開啟對話框以編輯當前薪資項目"""
        return {
            "type": "ir.actions.act_window",
            "name": "變更薪資規則",
            "res_model": "wizard.payslip.line.edit",
            "view_mode": "form",
            "target": "new",
            "context": {
                "default_payslip_line_id": self.id,
                "default_amount": self.amount,
            },
        }
        
    def recalculate_payslip_line(self):
        payslip = self.payslip_id
        employee = payslip.employee_id
        rule = self.salary_rule_id
        if rule.code == 'Labor':
            payslip.set_labor_insurance_salary()
        if rule.code == 'Healthy':
            payslip.set_health_insurance_salary()
        if rule.code == 'COMP_Occupational_Accident_Insurance':
            payslip.set_labor_harm_insurance_salary()
        rules_dict = {}
        categories = BrowsableObject(employee.id, {}, self.env)
        rules = BrowsableObject(employee.id, rules_dict, self.env)
        # 放置資料的容器dictionary(字典)，後面的python code跑safe_eval時所要用的變數都裝在裡面，甚至跑完的結果也會在裡面
        baselocaldict = payslip.get_baselocaldict(payslip)
        baselocaldict["categories"] = categories
        baselocaldict["rules"] = rules
        localdict = dict(baselocaldict, employee=employee)
        payslip_line = self
        result = payslip._compute_single_rule_recalculate(rule, employee, localdict, payslip, payslip_line)
        self.amount = result['amount']
        self.note = result['note']
        self.category_id = result['category_id']

    @api.depends('amount')
    def check_employee_setting(self):
        for rec in self:
            if rec.payslip_employee_setting_id.salary_amount == rec.amount or rec.payslip_id.state == 'confirm':
                rec.is_employee_setting = True
            else:
                rec.is_employee_setting = False