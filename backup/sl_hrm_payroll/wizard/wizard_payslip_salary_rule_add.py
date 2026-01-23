from odoo import api, fields, models
from datetime import date, timedelta
from odoo.exceptions import UserError

class WizardPayslipSalaryRuleAdd(models.TransientModel):
    _name = "wizard.payslip.salary.rule.add"
    _description = "新增薪資項目"

    salary_rule_id = fields.Many2one("hr.salary.rule", string="薪資規則", required=True)
    amount = fields.Float(string="金額", required=True)
    change_reason = fields.Text(string="異動原因")
    start_date = fields.Date(string="開始日期",)
    change_date = fields.Date(string="異動日期",)

    def apply_salary_rule(self):
        payslip = self.env["hr.payslip"].browse(self.env.context.get("active_id"))
        if self.salary_rule_id.id in payslip.payslip_line_ids.salary_rule_id.ids:
            raise UserError("已有該筆薪資明細")

        # 獲取員工
        employee = payslip.employee_id
        if not employee:
            return

        # 獲取員工的薪資結構
        if not employee.payroll_structure_id:
            raise UserError("該員工尚未設定薪資結構，請先設定。")

        # 將薪資規則新增至薪資結構
        structure = employee.payroll_structure_id
        if self.salary_rule_id.id not in structure.rule_ids.ids:
            structure.rule_ids = [(4, self.salary_rule_id.id)]

        employee.payslip_setting_ids.create(
            {
                "employee_id": employee.id,
                "salary_rule_id": self.salary_rule_id.id,
                "start_date": payslip.salary_date,
                "change_date": date.today(),
                "change_reason": self.change_reason,
                "salary_amount": self.amount,
            }
        )

        payslip.write({
            'payslip_line_ids': [(0, 0, {
                'name': self.salary_rule_id.name,
                'salary_rule_id': self.salary_rule_id.id,
                'category_id': self.salary_rule_id.category_id.id,
                'sequence': self.salary_rule_id.sequence,
                'code': self.salary_rule_id.code,
                'amount': self.amount,
            })]
        })
