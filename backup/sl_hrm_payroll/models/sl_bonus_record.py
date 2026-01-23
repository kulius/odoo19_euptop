from datetime import datetime,date
import logging

from odoo import models, api, fields

from dateutil.relativedelta import relativedelta


class StarryLordBonusRecord(models.Model):
    _name = 'sl.bonus.record'
    _description = '獎金發放紀錄'
    _rec_name = 'display_name'

    company_id = fields.Many2one(
        'res.company',
        string='公司',
        required=True,
        default=lambda self: self.env.company
    )
    employee_id = fields.Many2one('hr.employee.public', string='員工', required=True)
    user_id = fields.Many2one('res.users', string='User', related='employee_id.user_id', store=True)
    payroll_allocation_day = fields.Date(string='認列薪資日期', required=True)
    actual_pay_day = fields.Date(string='發放日', required=True)
    amount = fields.Float(string='金額', required=True)
    salary_rule_id = fields.Many2one(
        comodel_name='hr.salary.rule',
        string='薪資規則',
        required=True,
        domain="[('is_non_recurring', '=', True), ('company_id', '=', company_id)]",
    )
    note = fields.Text(string='備註')
    display_name = fields.Char(string='名稱', compute='compute_display_name', store=False, readonly=True)

    def compute_display_name(self):
        for record in self:
            record.display_name = '%s - %s %s' % (record.employee_id.name, record.payroll_allocation_day.strftime('%Y-%m'), record.salary_rule_id.name)

    def auto_create_bonus_record(self):
        # 查詢hr.employee在當月第一天與最後一天生日的資料
        last_day = fields.Date.today() + relativedelta(days=-1)
        # birthday的月份等於first_day當月
        birthday_employee_ids = self.env['hr.employee'].search([('month_of_birthday', '=', date.strftime(last_day, '%m'))])

        # 自動發放生日禮金(salary_rule_id.code='birthday_bonus')
        birthday_salary_rule_id = self.env['hr.salary.rule'].search([('code', '=', 'birthday_bonus')], limit=1)
        if birthday_salary_rule_id:
            for employee_id in birthday_employee_ids:
                self.env['sl.bonus.record'].create({
                    'employee_id': employee_id.id,
                    'payroll_allocation_day': fields.Date.today().replace(day=1),
                    'actual_pay_day': fields.Date.today(),
                    'amount': 1000,
                    'salary_rule_id': birthday_salary_rule_id.id,
                })

    def get_bonus_records_for_payslip(self, date_from, date_to):
        """取得指定員工、日期範圍和薪資代碼的調整項目（供薪資計算使用）"""
        domain = [
            ('payroll_allocation_day', '>=', date_from),
            ('payroll_allocation_day', '<=', date_to),
        ]
        return self.search(domain, order='employee_id')
    
class StarryLordPayslipSheetInheritAdjustment(models.Model):
    _inherit = "sl.hr.payslip.sheet"
    
    def compute_payslip_bonus(self):
        self.ensure_one()
        self.payslip_ids.unlink()
        bonus_records = self.env['sl.bonus.record'].get_bonus_records_for_payslip(
            self.date_from, self.date_to
        )

        for bonus_record in bonus_records:
            try:
                payslip_sheet = self
                payslip_id = self.payslip_ids.filtered(
                    lambda p: p.employee_id.id == bonus_record.employee_id.id
                )
                if not payslip_id:
                    payroll_structure_id = bonus_record.employee_id.payroll_structure_id
                    if not payroll_structure_id:
                        payroll_structure_id = self.env['hr.payroll.structure'].search([
                            ('company_id', '=', bonus_record.company_id.id),
                        ], limit=1)
                    payslip_id = self.env['hr.payslip'].create({
                        'employee_id': bonus_record.employee_id.id,
                        'date_from': self.date_from,
                        'date_to': self.date_to,
                        'sl_hr_payslip_sheet_id': self.id,
                        'payroll_structure_id': payroll_structure_id.id,
                    })
                    
                payslip_id.set_health_insurance_salary()
                salary_rule = self.env['hr.salary.rule'].search([
                    ('code', '=', bonus_record.salary_rule_id.code),
                    ('company_id', '=', bonus_record.company_id.id)
                ], limit=1)
                    
                self.env['hr.payslip.line'].create({
                    'payslip_id': payslip_id.id,
                    'employee_id': bonus_record.employee_id.id,
                    'salary_rule_id': salary_rule.id,
                    'amount': bonus_record.amount,
                    'category_id': salary_rule.category_id.id,
                    'sequence': salary_rule.sequence,
                    'name': salary_rule.name,
                    'code': salary_rule.code,
                    'manual': True,
                })
            except Exception as e:
                logging.error(f"獎金產生失敗：{str(e)}")
        self.compute_tax()
                
    def compute_tax(self):
        """計算薪資單的稅金"""
        for payslip in self.payslip_ids:
            tax_rules = ['WITHHOLDincome', 'health_insurance2.0_cost']
            for rule in tax_rules:
                salary_rule = self.env['hr.salary.rule'].search([
                    ('code', '=', rule),
                    ('company_id', '=', payslip.employee_id.company_id.id)
                ], limit=1)
                if salary_rule:
                    tax_line = self.env['hr.payslip.line'].create({
                        'payslip_id': payslip.id,
                        'employee_id': payslip.employee_id.id,
                        'salary_rule_id': salary_rule.id,
                        'amount': 0,
                        'category_id': salary_rule.category_id.id,
                        'sequence': salary_rule.sequence,
                        'name': salary_rule.name,
                        'code': salary_rule.code,
                    })
            payslip.recompute_auto_rules()