from odoo import models, fields, api
from dateutil.relativedelta import relativedelta
from calendar import monthrange
from decimal import Decimal, ROUND_HALF_UP


class HrPayslipExtension(models.Model):
    _inherit = "hr.payslip"

    @api.depends('sl_hr_payslip_sheet_id.salary_date')
    def _compute_salary_dates(self):
        for payslip in self:
            if payslip.sl_hr_payslip_sheet_id and payslip.sl_hr_payslip_sheet_id.salary_date:
                payslip.salary_date = payslip.sl_hr_payslip_sheet_id.salary_date
                payslip.date_from = payslip.sl_hr_payslip_sheet_id.date_from
                payslip.date_to = payslip.sl_hr_payslip_sheet_id.date_to

    @api.depends("payslip_line_ids.amount", "payslip_line_ids.salary_rule_id.is_non_recurring", "payslip_line_ids.salary_rule_id.category_id.code")
    def _compute_taxable_non_recurring_salary(self):
        for payslip in self:
            taxable_lines = payslip.payslip_line_ids.filtered(
                lambda line: line.salary_rule_id.category_id.code == 'Taxable_Add'
                and line.salary_rule_id.is_non_recurring
            )
            taxable_line_others = payslip.payslip_line_other_ids.filtered(
                lambda line: line.salary_rule_id.category_id.code == 'Taxable_Add'
                and line.salary_rule_id.is_non_recurring
            )
            payslip.computed_taxable_non_recurring_salary = sum(
                taxable_lines.mapped("amount")) + sum(taxable_line_others.mapped("amount"))

    @api.depends("payslip_line_ids.amount", "payslip_line_ids.salary_rule_id.is_non_recurring", "payslip_line_ids.salary_rule_id.category_id.code")
    def _compute_taxable_recurring_salary(self):
        for payslip in self:
            taxable_lines = payslip.payslip_line_ids.filtered(
                lambda line: line.salary_rule_id.category_id.code == 'Taxable_Add'
                and not line.salary_rule_id.is_non_recurring
            )
            taxable_line_others = payslip.payslip_line_other_ids.filtered(
                lambda line: line.salary_rule_id.category_id.code == 'Taxable_Add'
                and not line.salary_rule_id.is_non_recurring
            )
            payslip.computed_taxable_recurring_salary = sum(
                taxable_lines.mapped("amount")) + sum(taxable_line_others.mapped("amount"))

    @api.depends("payslip_line_ids.amount", "payslip_line_ids.salary_rule_id.is_non_recurring", "payslip_line_ids.salary_rule_id.category_id.code")
    def _computed_withholding_salary(self):
        for payslip in self:
            taxable_lines = payslip.payslip_line_ids.filtered(
                lambda line: (
                    line.salary_rule_id.is_withholding
                    and line.salary_rule_id.category_id.code != 'COMP'
                )
            )
            taxable_line_others = payslip.payslip_line_other_ids.filtered(
                lambda line: (
                    line.salary_rule_id.is_withholding
                    and line.salary_rule_id.category_id.code != 'COMP'
                )
            )
            payslip.computed_withholding_salary = sum(
                taxable_lines.mapped("amount")) + sum(taxable_line_others.mapped("amount"))

    @api.depends("computed_year_taxable_non_recurring_salary", "computed_taxable_non_recurring_salary")
    def _compute_pre_taxable_non_recurring_salary(self):
        for payslip in self:
            payslip.computed_pre_taxable_non_recurring_salary = (
                payslip.computed_year_taxable_non_recurring_salary -
                payslip.computed_taxable_non_recurring_salary
            )

    @api.depends('computed_taxable_non_recurring_salary', 'date_from', 'date_to')
    def _compute_year_taxable_non_recurring_salary(self):
        for payslip in self:
            payslip_date = fields.Date.from_string(payslip.date_from)
            payslip_year = payslip_date.year
            payslip_month = payslip_date.month
            last_day = monthrange(payslip_year, payslip_month)[1]

            domain = [
                ('employee_id', '=', payslip.employee_id.id),
                ('date_from', '>=', f'{payslip_year}-01-01'),
                ('date_to', '<=',
                 f'{payslip_year}-{payslip_month:02d}-{last_day}')
            ]
            yearly_payslips = self.search(domain)
            for yearly_payslip in yearly_payslips:
                print(yearly_payslip.date_from, yearly_payslip.date_to)
            payslip.computed_year_taxable_non_recurring_salary = sum(
                yearly_payslips.mapped('computed_taxable_non_recurring_salary'))

    @api.depends("health_insurance_salary")
    def _computed_health2_base(self):
        for record in self:
            record.computed_health2_base = record.health_insurance_salary * 4

    @api.depends('computed_taxable_recurring_salary', 'taxable_decrease_subtotal')
    def _computed_taxable_income(self):
        for payslip in self:
            payslip.computed_taxable_income = (
                payslip.computed_taxable_recurring_salary -
                payslip.taxable_decrease_subtotal
            )
            
    @api.depends('date_from', 'date_to', 'employee_id.registration_date', 'employee_id.resignation_date')
    def _computed_get_partial_month_ratio(self):
        for payslip in self:
            employee = payslip.employee_id
            if not employee.is_partial_month(payslip.date_from, payslip.date_to):
                payslip.computed_partial_month_ratio = 1
                continue
            ratio = self.true_round(
                employee.get_partial_month_ratio(
                    payslip.date_from, payslip.date_to
                ), 10
            )
            payslip.computed_partial_month_ratio = ratio
            
    @api.depends(
        'health_insurance_salary', 
        'computed_taxable_income', 
        'computed_taxable_non_recurring_salary', 
        'taxable_add_subtotal'
    )
    def _computed_get_salary_tax(self):
        for payslip in self:
            percentage = self.get_setting_param(
                'salary_withhold_tax_percentage') / 100
            base = self.get_setting_param('salary_withhold_tax_base')

            tax_amount, amount, valid_data = 0, 0, None

            pay_data = self.env['hr.health.insurance.history'].search(
                [('health_insurance_history_id', '=', payslip.employee_id.id)], order='start_date')
            if pay_data:
                valid_data = pay_data.filtered(lambda r: payslip.date_from >= r.start_date).sorted(
                    key='start_date', reverse=True)[:1]

            if valid_data:
                # 如果是正職員工，應稅加項要分成固定與非固定來計算
                for index, amount in enumerate([
                    payslip.computed_taxable_income,
                    payslip.computed_taxable_non_recurring_salary,
                ]):
                    if index == 0:
                        tax_amount += self.env['hr.salary.tax.gap'].get_cost(
                            amount, int(payslip.employee_id.dependents)
                        )
                    if index == 1 and amount >= base:
                        tax_amount += amount * percentage

            else:
                amount = payslip.taxable_add_subtotal
                if amount >= base:
                    tax_amount += amount * percentage

            payslip.computed_salary_tax = self.true_round(tax_amount)
            
    @api.depends(
        'health_insurance_salary', 
        'taxable_add_subtotal', 
        'computed_taxable_non_recurring_salary', 
        'computed_year_taxable_non_recurring_salary'
    )
    def _computed_get_health2(self):
        for payslip in self:
            percentage = self.get_setting_param(
                'health_insurance2_percentage') / 100
            multiple = self.get_setting_param('health_insurance2_base_multiple')

            supplementary_amount, bonus, valid_data = 0, 0, None

            year = payslip.date_from.replace(month=1, day=1)
            pay_data = self.env['hr.health.insurance.history'].search(
                [('health_insurance_history_id', '=', payslip.employee_id.id)], order='start_date')
            if pay_data:
                valid_data = pay_data.filtered(lambda r: payslip.date_from >= r.start_date).sorted(
                    key='start_date', reverse=True)[:1]

            if valid_data:
                # 如果有健保就只算獎金的部分
                # 不然就算是兼職，如果超過最低工資一樣要扣
                bonus = payslip.computed_taxable_non_recurring_salary

                charge = Decimal(valid_data.health_insurance_gap)
                cost_base = charge * multiple
            
                bonus_sum = payslip.computed_year_taxable_non_recurring_salary
                cost_base = min(bonus_sum - multiple * charge, bonus)
                maximum = self.get_setting_param('tax_base_maximum')
                cost_base = min(cost_base, maximum)
                cost_base = max(cost_base, 0)
                supplementary_amount = cost_base * percentage
            else:
                wage = self.get_setting_param(f"lowerst_monthly_wage_{year.year}")
                
                income = payslip.taxable_add_subtotal
                if income >= wage:
                    supplementary_amount = income * percentage
            payslip.computed_health2 = self.true_round(supplementary_amount)