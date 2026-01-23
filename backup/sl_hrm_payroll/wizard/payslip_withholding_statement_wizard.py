from odoo import models, fields, api
from datetime import date
import calendar


class PayslipWithholdingStatementWizard(models.TransientModel):
    _name = 'payslip.withholding.statement.wizard'
    _description = '薪資代扣申報精靈'

    start_date = fields.Date(string="開始日期", required=True,
        default=lambda self: date(date.today().year, 1, 1)
        )
    end_date = fields.Date(string="結束日期", 
        required=True,default=lambda self: date(date.today().year, 12, 31)
        )
    company_id = fields.Many2one(
        'res.company',
        string='公司',
        required=True,
        default=lambda self: self.env.company
    )
    city_agency = fields.Char(string="縣市機關別")
    serial_number = fields.Char(string="序號")
    reporting_unit_tax_id = fields.Char(string="申報單位統一編號", related="company_id.vat")
    income_note = fields.Char(string="所得註記")
    income_format = fields.Char(string="所得格式")
    payable_add_subtotal = fields.Char(string="扣繳憑單給付總額")
    withholding_tax = fields.Char(string="扣繳憑單扣繳稅額")
    net_payment = fields.Char(string="扣繳憑單給付淨額")
    recipient_tax_id = fields.Char(string="所得人統編", related="company_id.vat")
    id_type = fields.Char(string="證號別")
    tax_credit_ratio = fields.Char(string="稅額扣抵比率%")
    allocation_count = fields.Char(string="分配次數")
    ex_dividend_date = fields.Char(string="除權(息)基準-年月日")
    software_note = fields.Char(string="軟體註記")
    error_note = fields.Char(string="錯誤註記")
    payment_year = fields.Char(string="所得給付年度")
    recipient_name = fields.Char(string="所得人姓名")
    recipient_address = fields.Char(string="所得人地址")
    income_period = fields.Char(string="所得所屬期間")
    other_cash_dividend = fields.Char(string="其他現金股利")
    capital_reserve_cash_dividend = fields.Char(string="資本公積現金股利")
    stock_dividend = fields.Char(string="股票股利")
    stock_dividend_shares = fields.Char(string="股票股利股數")
    tax_credit_note = fields.Char(string="扣抵稅額註記")
    statement_issue_method = fields.Char(string="憑單填發方式")
    is_over_183_days = fields.Char(string="是否滿183天")
    residence_country_code = fields.Char(string="居住地國或地區代碼")
    tax_treaty_code = fields.Char(string="租稅協定代碼")
    liquidation_date = fields.Char(string="清算完結日期")
    tax_identification_number = fields.Char(string="稅務識別碼")

    def set_this_month(self):
        for rec in self:
            today = date.today()
            rec.start_date = today.replace(day=1)
            rec.end_date = today.replace(
                day=calendar.monthrange(today.year, today.month)[1]
            )
        return self.reopen_wizard()

    def set_this_year(self):
        for rec in self:
            today = date.today()
            rec.start_date = date(today.year, 1, 1)
            rec.end_date = date(today.year, 12, 31)
        return self.reopen_wizard()

    def set_pre_year(self):
        for rec in self:
            today = date.today()
            rec.start_date = date(today.year - 1, 1, 1)
            rec.end_date = date(today.year - 1, 12, 31)
        return self.reopen_wizard()
    
    def reopen_wizard(self):
        return {
            'type': 'ir.actions.act_window',
            'name': '薪資代扣申報',
            'res_model': 'payslip.withholding.statement.wizard',
            'view_mode': 'form',
            'res_id': self.id,
            'target': 'new',
        }       
        
    def view_withholding_statement(self):
        return self.env.ref('sl_hrm_payroll.action_payslip_withholding_statement_report').report_action(self, data={
            'form': self.read()[0],
            'sheet_name': '薪資扣繳憑單',
        })
       