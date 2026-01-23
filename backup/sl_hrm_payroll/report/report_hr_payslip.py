from datetime import date, datetime, time, timedelta
import math
import babel
from dateutil.relativedelta import relativedelta
from pytz import timezone

from odoo import _, api, fields, models, tools
from odoo.exceptions import UserError, ValidationError


class ReportHrPayslip(models.AbstractModel):
    _name = 'report.sl_hrm_payroll.report_hr_payslip'

    @api.model
    def _get_report_values(self, docids, data=None):
        docs = self.env['hr.payslip'].browse(docids)
        all_payslip = []
        for doc in docs:
            comp_labor_pension = 0
            add_subtotal_line = []
            other_add_subtotal_line = []
            decrease_subtotal_line = []
            other_decrease_subtotal_line = []
            comp_labor_pension = doc.payslip_line_ids.filtered(lambda x: x.code == 'COMP_Labor_Pension').amount
            basic_wage_sum = sum(line.amount for line in doc.payslip_line_ids
                                 if line.salary_rule_id.is_basic
                                 )
            for payslip_line in doc.payslip_line_ids:
                # if payslip_line.code == 'COMP_Labor_Pension':
                #     comp_labor_pension = payslip_line.amount
                if payslip_line.category_id.code in ['Taxable_Add', 'Taxfree_Add']:
                    add_subtotal_line.append(payslip_line)
            for payslip_line in doc.payslip_line_other_ids:
                if payslip_line.category_id.code in ['Taxable_Add', 'Taxfree_Add']:
                    other_add_subtotal_line.append(payslip_line)

            for payslip_line in doc.payslip_line_ids.sorted(lambda x: x.salary_rule_id.sequence):
                if payslip_line.category_id.code in ['Taxable_Decrease', 'Taxfree_Decrease']:
                    decrease_subtotal_line.append(payslip_line)
            for payslip_line in doc.payslip_line_other_ids:
                if payslip_line.category_id.code in ['Taxable_Decrease', 'Taxfree_Decrease']:
                    other_decrease_subtotal_line.append(payslip_line)

            all_value = {'employee_id': doc.employee_id.name, 'name': doc.name, 'date_from': doc.date_from,
                         'date_to': doc.date_to, 'payslip_line_ids': doc.payslip_line_ids,
                         'add_subtotal_line': add_subtotal_line,
                         'other_add_subtotal_line': other_add_subtotal_line,
                         'add_subtotal': doc.taxable_add_subtotal + doc.taxfree_add_subtotal,
                         'decrease_subtotal_line': decrease_subtotal_line,
                         'other_decrease_subtotal_line': other_decrease_subtotal_line,
                         'decrease_subtotal': doc.taxable_decrease_subtotal + doc.taxfree_decrease_subtotal,
                         'labor_insurance_salary': doc.labor_insurance_salary,
                         'health_insurance_salary': doc.health_insurance_salary,
                         'labor_pension_salary': doc.labor_pension_salary,
                         'labor_harm_insurance_salary': doc.labor_harm_insurance_salary,
                         'comp_labor_pension': comp_labor_pension,
                         'basic_wage_sum': basic_wage_sum,
                         'over_tax_amount': doc.over_tax_amount,
                         'payroll_allocation_day': doc.salary_date.strftime('%Y-%m'),
                         'actual_pay_day': doc.actual_pay_day.strftime('%Y-%m-%d'),
                         'all_subtotal': f"{doc.all_subtotal:.0f}",
                         'note': doc.note}
            all_payslip.append(all_value)

        return {'docs': docs, 'all_payslip': all_payslip, 'data': data}

