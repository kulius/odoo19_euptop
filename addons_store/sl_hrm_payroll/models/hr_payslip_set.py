from odoo import models, fields, api


class HrPayslipExtension(models.Model):
    _inherit = "hr.payslip"

    def set_health_insurance_salary(self):
        for payslip in self:
            payslip.health_insurance_salary = 0
            if not payslip.employee_id or not payslip.date_from:
                continue  # 避免錯誤

            history_data = self.env['hr.health.insurance.history'].search(
                [('health_insurance_history_id', '=', payslip.employee_id.id)],
                order='start_date'
            )

            if history_data:
                valid_data = history_data.filtered(lambda r: payslip.date_from >= r.start_date).sorted(
                    key=lambda r: r.start_date, reverse=True
                )[:1]

                if valid_data:
                    interval = valid_data[0].health_insurance_gap
                    payslip.health_insurance_salary = interval
                    
    def set_labor_insurance_salary(self):
        for payslip in self:
            payslip.labor_insurance_salary = 0
            if not payslip.employee_id or not payslip.date_from:
                continue  # 避免錯誤

            history_data = self.env['hr.labor.insurance.history'].search(
                [('labor_insurance_history_id', '=', payslip.employee_id.id)],
                order='start_date'
            )

            if history_data:
                valid_data = history_data.filtered(lambda r: payslip.date_from >= r.start_date).sorted(
                    key=lambda r: r.start_date, reverse=True
                )[:1]

                if valid_data:
                    interval = valid_data[0].labor_insurance_gap
                    payslip.labor_insurance_salary = interval
                    
    def set_labor_harm_insurance_salary(self):
        for payslip in self:
            payslip.labor_harm_insurance_salary = 0
            if not payslip.employee_id or not payslip.date_from:
                continue  # 避免錯誤

            history_data = self.env['hr.labor.harm.insurance.history'].search(
                [('employee_id', '=', payslip.employee_id.id)],
                order='start_date'
            )

            if history_data:
                valid_data = history_data.filtered(lambda r: payslip.date_from >= r.start_date).sorted(
                    key=lambda r: r.start_date, reverse=True
                )[:1]

                if valid_data:
                    interval = valid_data[0].insurance_salary
                    payslip.labor_harm_insurance_salary = interval