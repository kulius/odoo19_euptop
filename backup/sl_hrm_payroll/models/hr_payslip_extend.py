from odoo import models, fields, api
from decimal import Decimal, ROUND_HALF_UP
from odoo.exceptions import UserError

class HrPayslipExtension(models.Model):
    _inherit = "hr.payslip"

    computed_taxable_recurring_salary = fields.Integer(
        string="當月薪資總計(經常性給與)",
        compute="_compute_taxable_recurring_salary",
        store=True
    )

    computed_pre_taxable_non_recurring_salary = fields.Integer(
        string="當月前獎金累計(非經常性給與)",
        compute="_compute_pre_taxable_non_recurring_salary",
        store=True
    )

    computed_taxable_non_recurring_salary = fields.Integer(
        string="當月獎金總計(非經常性給與)",
        compute="_compute_taxable_non_recurring_salary",
        store=True
    )

    computed_year_taxable_non_recurring_salary = fields.Integer(
        string="當年度獎金累計(非經常性給與)",
        compute="_compute_year_taxable_non_recurring_salary",
        store=True
    )

    computed_withholding_salary = fields.Integer(
        string="當月稅費代扣總計",
        compute="_computed_withholding_salary",
        store=True
    )

    computed_taxable_income = fields.Integer(
        string="應稅薪資所得",
        compute="_computed_taxable_income",
        store=True
    )

    computed_health2_base = fields.Integer(
        string="四倍投健保級距",
        compute="_computed_health2_base",
        store=True
    )
    
    computed_partial_month_ratio = fields.Float(
        string="在職天數比例",
        compute="_computed_get_partial_month_ratio",
        store=True
    )
    
    computed_salary_tax = fields.Float(
        string="所得稅",
        compute="_computed_get_salary_tax",
        store=True
    )
    
    computed_health2 = fields.Float(
        string="二代健保",
        compute="_computed_get_health2",
        store=True
    )

    def healthy_insurance2(self, payslip, categories):        
        payslip = self.env['hr.payslip'].browse(payslip.id)
        manual_line = self.get_manual_line(payslip, "health_insurance2.0_cost")
        if manual_line:
            return manual_line.amount if manual_line else 0.0
        
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

        return self.true_round(supplementary_amount)
    
    def labor_harm_insurance(self, payslip, categories):
        rate = self.get_setting_param('work_accident_rate') / 100  # 職業災害費率
        amount = rate * payslip.dict.labor_harm_insurance_salary
        return self.true_round(amount)
            
    def withhold_income_tax(self, payslip, categories):
        payslip = self.env['hr.payslip'].browse(payslip.id)
        manual_line = self.get_manual_line(payslip, "WITHHOLDincome")
        if manual_line:
            return manual_line.amount if manual_line else 0.0
        
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

        return self.true_round(tax_amount)

    def true_round(self, value, precision=0):
        """
        精確四捨五入函式
        :param value: 要四捨五入的數字 (可以是 float, int, 或 str)
        :return: 四捨五入後的 Decimal 值
        """
        decimal_value = Decimal(str(value))
        rounding_format = Decimal(f"1e-{precision}")
        return decimal_value.quantize(rounding_format, rounding=ROUND_HALF_UP)
          
    def get_setting_param(self, key, accept_zero=False, is_str=False, default=None):
        setting = self.env['ir.config_parameter'].sudo()
        param = setting.get_param(key, default=default)
        if param is None:
            raise UserError(f"系統參數{key}未設定")
        if is_str:
            return param
        param = self.true_round(param, 5)
        if not accept_zero and  param == 0:
            raise UserError(f"系統參數{key}不可設定為零")
        return param
    
    def recompute_auto_rules(self):
        # 如所得稅或二代健保受其他項目影響，要重算
        # 所以在薪資結構那邊可以設定自動重算的項目
        for payslip in self:
            structure = payslip.employee_id.payroll_structure_id
            for rule in structure.auto_recompute_rule_ids:
                lines = payslip.payslip_line_ids.filtered(lambda l: l.salary_rule_id.id == rule.id)
                for line in lines:
                    line.recalculate_payslip_line()

    def get_manual_line(self, payslip, code):
        # 萬一系統自動計算的有錯，可以把手動調整打勾，這樣就會使用手動調整的金額
        manual_line = payslip.payslip_line_ids.filtered(
            lambda l: l.salary_rule_id.code == code and l.manual
        )
        return manual_line if manual_line else False