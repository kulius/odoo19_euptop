from odoo import _, fields, models
from odoo.exceptions import UserError


class WizardPayslipSelectEmployee(models.TransientModel):
    _name = "wizard.payslip.select.employee"
    _description = "選擇員工"

    employee_ids = fields.Many2many(
        "hr.employee", "wizard_payslip_select_employee_rel", "wizard_id", "employee_id", "Employees"
    )
