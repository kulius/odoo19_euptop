from odoo import models, api
from types import SimpleNamespace
from datetime import date, datetime

class PayslipSheetReportTemplate(models.AbstractModel):
    _name = 'report.sl_hrm_payroll.payslip_sheet_report_template'
    _description = '每月薪資明細報表'

    @api.model
    def _get_report_values(self, docids, data=None):
        form_data = data['form']
        report_type = data.get('report_type', 'all')
        sheet_name = data.get('sheet_name', '薪資明細表')

        sheet_id = form_data['sheet_id'][0]
        sheet = self.env['sl.hr.payslip.sheet'].browse(sheet_id)
        payslips = sheet.payslip_ids.sorted(
            key=lambda p: (
                p.employee_id.department_id.name or '',
                p.employee_id.employee_number or ''
            )
        )

        salary_rules_set = set()
        computeds_set = ['payable_add_subtotal', 'all_subtotal']
        employee_data = []
        total_salary_lines = {}
        total_computed = {
            'payable_add_subtotal': 0.0,
            'all_subtotal': 0.0,
        }

        for payslip in payslips:
            salary_lines = {}
            total_computed['payable_add_subtotal'] += payslip.payable_add_subtotal
            total_computed['all_subtotal'] += payslip.all_subtotal

            lines = self._get_filtered_lines(payslip, report_type)
            for line in lines:
                rule_id = line.salary_rule_id.id
                salary_lines[rule_id] = line.amount if line.amount != 0 else ''
                salary_rules_set.add(line.salary_rule_id)

                # 累加總計
                if rule_id not in total_salary_lines:
                    total_salary_lines[rule_id] = 0
                total_salary_lines[rule_id] += line.amount

            computeds = {
                'payable_add_subtotal': payslip.payable_add_subtotal if payslip.payable_add_subtotal != 0 else '',
                'all_subtotal': payslip.all_subtotal if payslip.all_subtotal != 0 else '',
            }

            employee_data.append({
                'employee': payslip.employee_id,
                'employee_number': payslip.employee_id.employee_number,
                'department': payslip.employee_id.department_id.name,
                'salary_lines': salary_lines,
                'computeds': computeds,
            })

        total_row = {
            'employee': SimpleNamespace(name='總計'),
            'employee_number': '',
            'department': '',
            'salary_lines': total_salary_lines,
            'computeds': total_computed,
            'is_total': True,
        }

        employee_data.insert(0, total_row)

        salary_rules = sorted(list(salary_rules_set), key=lambda r: r.sequence)

        sheet_name += ' - ' + sheet.name

        return {
            'doc_ids': docids,
            'doc_model': 'hr.payslip',
            'data': data['form'],
            'employees': employee_data,
            'salary_rules': salary_rules,
            'computeds': computeds_set,
            'sheet': sheet,
            'sheet_name': sheet_name,
        }

    def _get_filtered_lines(self, payslip, report_type):
        """根據報表類型篩選薪資明細行."""
        lines = sorted(
            list(payslip.payslip_line_ids) +
            list(payslip.payslip_line_other_ids),
            key=lambda l: l.salary_rule_id.sequence
        )
        if report_type == 'pay':
            lines = [
                line for line in lines if line.salary_rule_id.category_id.code != 'COMP']
        elif report_type == 'cost':
            lines = [
                line for line in lines if line.salary_rule_id.category_id.code != 'Taxfree_Decrease']
        elif report_type == 'all':
            lines = lines
        # lines = payslip
        return lines


class PayslipBonusSheetReportTemplate(models.AbstractModel):
    _name = 'report.sl_hrm_payroll.payslip_bonus_sheet_report_template'
    _description = '獎金發放明細報表'

    @api.model
    def _get_report_values(self, docids, data=None):
        form_data = data['form']
        sheet_name = data.get('sheet_name', '獎金發放明細表')

        sheet_id = form_data['sheet_id'][0]
        sheet = self.env['sl.hr.payslip.sheet'].browse(sheet_id)
        payslips = sheet.payslip_ids.sorted(
            key=lambda p: (
                p.employee_id.department_id.name or '',
                p.employee_id.employee_number or ''
            )
        )

        salary_rules_set = set()
        computeds_set = ['payable_add_subtotal', 'computed_salary_tax', 'computed_health2', 'all_subtotal']
        employee_data = []
        total_computed = {
            'payable_add_subtotal': 0.0,
            'computed_salary_tax': 0.0,
            'computed_health2': 0.0,
            'all_subtotal': 0.0,
        }

        for payslip in payslips:
            total_computed['payable_add_subtotal'] += payslip.payable_add_subtotal
            total_computed['all_subtotal'] += payslip.all_subtotal
            total_computed['computed_salary_tax'] += payslip.computed_salary_tax
            total_computed['computed_health2'] += payslip.computed_health2

            computeds = {
                'payable_add_subtotal': payslip.payable_add_subtotal if payslip.payable_add_subtotal != 0 else '',
                'all_subtotal': payslip.all_subtotal if payslip.all_subtotal != 0 else '',
                'computed_salary_tax': payslip.computed_salary_tax if payslip.computed_salary_tax != 0 else '',
                'computed_health2': payslip.computed_health2 if payslip.computed_health2 != 0 else '',
            }

            employee_data.append({
                'employee': payslip.employee_id,
                'employee_number': payslip.employee_id.employee_number,
                'department': payslip.employee_id.department_id.name,
                'computeds': computeds,
            })

        total_row = {
            'employee': SimpleNamespace(name='總計'),
            'employee_number': '',
            'department': '',
            'computeds': total_computed,
            'is_total': True,
        }

        employee_data.insert(0, total_row)

        salary_rules = sorted(list(salary_rules_set), key=lambda r: r.sequence)

        sheet_name += ' - ' + sheet.name

        return {
            'doc_ids': docids,
            'doc_model': 'hr.payslip',
            'data': data['form'],
            'employees': employee_data,
            'salary_rules': salary_rules,
            'computeds': computeds_set,
            'sheet': sheet,
            'sheet_name': sheet_name,
        }

class PayslipWithholdingStatementTemplate(models.AbstractModel):
    _name = 'report.sl_hrm_payroll.payslip_withholding_statement_template'
    _description = '所得申報報表'

    @api.model
    def _get_report_values(self, docids, data=None):
        form_data = data['form']
        sheet_name = data.get('sheet_name', '所得申報報表')

        sheet_ids = self.env['sl.hr.payslip.sheet'].search([
            ('pay_date', '>=', form_data['start_date']),
            ('pay_date', '<=', form_data['end_date']),
            ('is_salary_sheet', '=', True),
        ])

        all_payslips = sheet_ids.mapped('payslip_ids')
        
        payslips_by_employee = {}
        for payslip in all_payslips:
            employee_id = payslip.employee_id.id
            if employee_id not in payslips_by_employee:
                payslips_by_employee[employee_id] = []
            payslips_by_employee[employee_id].append(payslip)

        computeds_set = ['payable_add_subtotal', 'withholding_tax', 'retire_amount', 'net_payment']
        employee_data = []
        total_computed = {
            'payable_add_subtotal': 0.0,
            'withholding_tax': 0.0,
            'retire_amount': 0.0,
            'net_payment': 0.0,
        }

        for employee_id, payslips in payslips_by_employee.items():
            employee = payslips[0].employee_id
            
            total_payable = sum(payslip.payable_add_subtotal for payslip in payslips)
            
            total_retire = 0.0
            withholding_tax = 0.0
            for payslip in payslips:
                retire_lines = payslip.payslip_line_ids.filtered(lambda line: line.salary_rule_id.code == 'Retire')
                total_retire += sum(line.amount for line in retire_lines)
                withholding_tax = payslip.computed_salary_tax if payslip.computed_salary_tax else 0.0
            
            net_payment = total_payable - total_retire
            
            total_computed['payable_add_subtotal'] += total_payable
            total_computed['withholding_tax'] += withholding_tax
            total_computed['retire_amount'] += total_retire
            total_computed['net_payment'] += net_payment

            computeds = {
                'payable_add_subtotal': total_payable if total_payable != 0 else '',
                'withholding_tax': withholding_tax if withholding_tax != 0 else '',
                'net_payment': net_payment if net_payment != 0 else '',
                'retire_amount': total_retire if total_retire != 0 else '',
            }

            row_data = self.fields_data_handler(form_data)
            row_data['recipient_name'] = employee.name
            row_data['recipient_address'] = employee.zip
            row_data['payable_add_subtotal'] = computeds['payable_add_subtotal']
            row_data['withholding_tax'] = computeds['withholding_tax']
            row_data['net_payment'] = computeds['net_payment']
            employee_data.append({
                'employee': employee,
                'employee_number': employee.employee_number,
                'department': employee.department_id.name,
                'computeds': computeds,
                'row_data': row_data,
            })

        employee_data.sort(key=lambda x: (x['department'] or '', x['employee_number'] or ''))

        total_row_data = self.fields_data_handler(form_data)
        total_row = {
            'employee': SimpleNamespace(name='總計'),
            'employee_number': '',
            'department': '',
            'computeds': total_computed,
            'row_data': total_row_data,
            'is_total': True,
        }

        # employee_data.insert(0, total_row)
        year = datetime.strptime(form_data['start_date'], "%Y-%m-%d").date().year
        sheet_name = str(year - 1911) + sheet_name

        form_fields = self.get_fields()
        form_string = self.fields_string_handler()
        return {
            'doc_ids': docids,
            'doc_model': 'hr.payslip',
            'data': data['form'],
            'employees': employee_data,
            'salary_rules': [],
            'computeds': computeds_set,
            'year': year,
            'start_date': form_data['start_date'],
            'end_date': form_data['end_date'],
            'sheet_name': sheet_name,
            'form_fields': form_fields,
            'form_string': form_string,
        }

    def fields_data_handler(self, form_data):
        form_data = {field: form_data.get(field) for field in self.get_fields()}
        return form_data

    def fields_string_handler(self):
        model = self.env['payslip.withholding.statement.wizard']
        form_string = [model._fields[field].string if field in model._fields else '' for field in self.get_fields()]
        return form_string

    def get_fields(self):
        return [
            'city_agency',
            'serial_number',
            'payable_add_subtotal',
            'withholding_tax',
            'net_payment',
            'reporting_unit_tax_id',
            'income_note',
            'income_format',
            'recipient_tax_id',
            'id_type',
            'tax_credit_ratio',
            'allocation_count',
            'ex_dividend_date',
            'software_note',
            'error_note',
            'payment_year',
            'recipient_name',
            'recipient_address',
            'income_period',
            'other_cash_dividend',
            'capital_reserve_cash_dividend',
            'stock_dividend',
            'stock_dividend_shares',
            'tax_credit_note',
            'statement_issue_method',
            'is_over_183_days',
            'residence_country_code',
            'tax_treaty_code',
            'liquidation_date',
            'tax_identification_number',
        ]