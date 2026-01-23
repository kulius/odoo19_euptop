from odoo import api, fields, models
from datetime import date, timedelta
from odoo.exceptions import ValidationError


class WizardPayslipLineEdit(models.TransientModel):
    _name = "wizard.payslip.line.edit"
    _description = "變更薪資規則"

    payslip_line_id = fields.Many2one(
        "hr.payslip.line", string="薪資規則", invisible=True
    )
    amount = fields.Float(string="金額", required=True)
    change_reason = fields.Text(string="異動原因")

    def save_changes(self):
        """保存編輯的內容"""
        if not self.payslip_line_id:
            return

        payslip_line_id = self.env.context.get("default_payslip_line_id")
        payslip_line = self.env["hr.payslip.line"].browse(payslip_line_id)
        salary_date = self._get_salary_date(payslip_line)

        employee = payslip_line.payslip_id.employee_id

        if not employee:
            raise ValidationError("無法找到對應的員工")

        self._update_employee_payslip_settings(employee, salary_date)

        self._recompute_payslip(self.payslip_line_id.payslip_id)

    def _update_employee_payslip_settings(self, employee, salary_date):
        """更新員工的薪資設定"""
        settings = self.env["starrylord.employee.payslip.setting"].search(
            [("employee_id", "=", employee.id)]
        )
        rule_setting = settings.filtered(
            lambda s: s.salary_rule_id.id == self.payslip_line_id.salary_rule_id.id
        )

        existing_setting = rule_setting.filtered(lambda s: s.start_date == salary_date)

        if existing_setting and existing_setting.start_date == salary_date:
            existing_setting.write(
                {
                    "salary_amount": self.amount,
                    "change_reason": self.change_reason,
                    "change_date": date.today(),
                }
            )
        else:
            self.env["starrylord.employee.payslip.setting"].create(
                {
                    "employee_id": employee.id,
                    "salary_rule_id": self.payslip_line_id.salary_rule_id.id,
                    "start_date": salary_date,
                    "change_date": date.today(),
                    "change_reason": self.change_reason,
                    "salary_amount": self.amount,
                }
            )

    def _recompute_payslip(self, payslip):
        """重算薪資"""
        if not payslip:
            raise ValidationError("無法找到對應的薪資單")
        payslip.compute_sheet()


    def _get_salary_date(self, payslip_line):
        payslip_sheet = payslip_line.payslip_id
        if payslip_sheet:
            return payslip_sheet.salary_date
        else:
            return date.today()
