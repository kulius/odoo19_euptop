from odoo import models, fields, api


class PayslipSheetReportWizard(models.TransientModel):
    _name = 'payslip.sheet.report.wizard'
    _description = 'Monthly Salary Wizard'

    sheet_id = fields.Many2one(
        'sl.hr.payslip.sheet',
        string="選擇薪資單",
        required=True,
    )
    
    blank = fields.Char(string="", default="")

    def view_pay_report(self):
        return self.env.ref('sl_hrm_payroll.action_payslip_sheet_report').report_action(self, data={
            'form': self.read()[0],
            'report_type': 'pay',
            'sheet_name': '薪資放款明細表',
        })
        
    def view_cost_report(self):
        return self.env.ref('sl_hrm_payroll.action_payslip_sheet_report').report_action(self, data={
            'form': self.read()[0],
            'report_type': 'cost',
            'sheet_name': '薪資成本明細表',
        })
        
    def view_report(self):
        return self.env.ref('sl_hrm_payroll.action_payslip_sheet_report').report_action(self, data={
            'form': self.read()[0],
            'report_type': 'all',
            'sheet_name': '薪資明細表',
        })
        
    def view_bonus_report(self):
        return self.env.ref('sl_hrm_payroll.action_payslip_bonus_sheet_report').report_action(self, data={
            'form': self.read()[0],
            'report_type': 'all',
            'sheet_name': '獎金明細表',
        })
        
    def view_pivot_report(self):
        self.ensure_one()
        action = self.env.ref('sl_hrm_payroll.hr_payslip_line_pivot_action').read()[0]
        payslip_ids = self.sheet_id.payslip_ids.ids
        action['domain'] = [('payslip_id', 'in', payslip_ids)]
        return action
