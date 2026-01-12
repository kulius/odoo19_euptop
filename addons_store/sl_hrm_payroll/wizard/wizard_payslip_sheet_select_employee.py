from odoo import _, fields, models
from odoo.exceptions import UserError


class WizardPayslipSelectEmployee(models.TransientModel):
    _name = "wizard.payslip.select.employee"
    _description = "選擇員工"

    employee_ids = fields.Many2many(
        "hr.employee", "hr_employee_payslip_batch_processing", "payslip_sheet_id", "employee_id", "Employees"
    )
