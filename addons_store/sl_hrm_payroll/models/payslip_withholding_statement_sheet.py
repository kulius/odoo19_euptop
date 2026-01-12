from dateutil.relativedelta import relativedelta
from odoo import models, fields, api
from datetime import date
import calendar
import base64


class PayslipWithholdingStatementSheet(models.Model):
    _name = 'payslip.withholding.statement.sheet'
    _description = '薪資代扣申報總表'
    
    name = fields.Char(string='申報單-標題', compute='compute_name', readonly=False, store=True)
    apply_year = fields.Date(string='申報年度', required=True, default=lambda self: date(date.today().year - 1, 1, 1))
    date_from = fields.Date(string='申報起算日', required=True, default=lambda self: date(date.today().year - 1, 1, 1))
    date_to = fields.Date(string='申報結算日', required=True, default=lambda self: date(date.today().year - 1, 12, 31))
    company_id = fields.Many2one(
        'res.company',
        string='公司',
        required=True,
        default=lambda self: self.env.company
    )
    statement_ids = fields.One2many(
        'payslip.withholding.statement',
        'statement_sheet_id',
        string='薪資代扣申報表',
        required=True
    )
    
    city_agency = fields.Char(string="縣市機關別", default='A09')
    serial_number = fields.Char(string="序號")
    reporting_unit_tax_id = fields.Char(string="申報單位統一編號", related="company_id.vat")
    income_note = fields.Char(string="所得註記")
    income_format = fields.Char(string="所得格式", default='50')
    payable_add_subtotal = fields.Char(string="扣繳憑單給付總額")
    withholding_tax = fields.Char(string="扣繳憑單扣繳稅額")
    net_payment = fields.Char(string="扣繳憑單給付淨額")
    recipient_tax_id = fields.Char(string="所得人統編")
    id_type = fields.Char(string="證號別", default='0')
    tax_credit_ratio = fields.Char(string="稅額扣抵比率%")
    allocation_count = fields.Char(string="分配次數")
    ex_dividend_date = fields.Char(string="除權(息)基準-年月日")
    software_note = fields.Char(string="軟體註記")
    error_note = fields.Char(string="錯誤註記")
    payment_year = fields.Char(string="所得給付年度", compute='_compute_payment_year', readonly=False)
    recipient_name = fields.Char(string="所得人姓名")
    recipient_address = fields.Char(string="所得人地址")
    income_period = fields.Char(string="所得所屬期間", compute='_compute_income_period', readonly=False)
    self_retire = fields.Char(string="自提勞退")
    capital_reserve_cash_dividend = fields.Char(string="資本公積現金股利")
    stock_dividend = fields.Char(string="股票股利")
    stock_dividend_shares = fields.Char(string="股票股利股數")
    tax_credit_note = fields.Char(string="扣抵稅額註記")
    statement_issue_method = fields.Char(string="憑單填發方式", default='1')
    is_over_183_days = fields.Char(string="是否滿183天")
    residence_country_code = fields.Char(string="居住地國或地區代碼")
    tax_treaty_code = fields.Char(string="租稅協定代碼")
    liquidation_date = fields.Char(string="檔案製作日期", compute='_compute_liquidation_date', readonly=False)
    tax_identification_number = fields.Char(string="稅務識別碼")
    blank = fields.Char(string="空白")
    blank2 = fields.Char(string="空白")

    @api.depends('name', 'apply_year')
    def compute_name(self):
        for rec in self:
            rec.name = rec.apply_year.strftime('%Y年') + '薪資代扣申報表'

    @api.onchange('apply_year')
    def onchange_apply_year(self):
        if self.apply_year:
            # 自動帶入薪資計算起迄第一天跟最後一天
            self.date_from = self.apply_year.replace(day=1, month=1)
            self.date_to = self.apply_year.replace(month=12, day=31)
    @api.depends('apply_year')
    def _compute_payment_year(self):
        for rec in self:
            if rec.apply_year:
                rec.payment_year = (rec.apply_year.year - 1911)
    @api.depends('payment_year')
    def _compute_income_period(self):
        for rec in self:
            if rec.payment_year:
                rec.income_period = f"{rec.payment_year}01{rec.payment_year}12"

    def _compute_liquidation_date(self):
        for rec in self:
            today = date.today()
            rec.liquidation_date = today.strftime('%m%d')

    def general_statement(self):
        """生成薪資代扣申報表紀錄"""
        # 清除現有的申報表紀錄
        self.statement_ids.unlink()
        
        # 根據起迄日期查詢薪資單
        sheet_ids = self.env['sl.hr.payslip.sheet'].search([
            ('pay_date', '>=', self.date_from),
            ('pay_date', '<=', self.date_to),
            ('is_salary_sheet', '=', True),
        ])
        
        all_payslips = sheet_ids.mapped('payslip_ids')
        
        # 按員工分組薪資單
        payslips_by_employee = {}
        for payslip in all_payslips:
            employee_id = payslip.employee_id.id
            if employee_id not in payslips_by_employee:
                payslips_by_employee[employee_id] = []
            payslips_by_employee[employee_id].append(payslip)
        
        # 為每個員工創建申報表紀錄
        statement_vals_list = []
        serial_number = 1
        for employee_id, payslips in payslips_by_employee.items():
            employee = payslips[0].employee_id
            
            # 計算薪資相關金額
            total_payable = sum(payslip.payable_add_subtotal for payslip in payslips)
            
            # 計算勞退自提總額
            total_retire = 0.0
            withholding_tax = 0.0
            for payslip in payslips:
                retire_lines = payslip.payslip_line_ids.filtered(
                    lambda line: line.salary_rule_id.code == 'Retire'
                )
                retire_lines_other = payslip.payslip_line_other_ids.filtered(
                    lambda line: line.salary_rule_id.code == 'Retire'
                )
                total_retire += sum(line.amount for line in retire_lines)
                total_retire += sum(line.amount for line in retire_lines_other)
                # 取最後一筆薪資單的扣繳稅額
                if payslip.computed_salary_tax:
                    withholding_tax = payslip.computed_salary_tax
            
            net_payment = total_payable - withholding_tax
            
            # 準備申報表資料，繼承上層的設定
            statement_vals = {
                'statement_sheet_id': self.id,
                'employee_id': employee.id,  # 必填欄位
            }
            
            # 繼承上層的預設值
            fields_mapping = self._get_field_mapping()
            for field_name, field_label in fields_mapping:
                statement_vals[field_name] = getattr(self, field_name, '')
                
            # 覆寫計算後的金額欄位
            statement_vals['payable_add_subtotal'] = str(total_payable) if total_payable else ''
            statement_vals['withholding_tax'] = str(withholding_tax) if withholding_tax else ''
            statement_vals['net_payment'] = str(net_payment) if net_payment else ''
            statement_vals['self_retire'] = str(total_retire) if total_retire else ''
            statement_vals['serial_number'] = str(serial_number).zfill(8)
            statement_vals['recipient_tax_id'] = employee.identification_id or ''
            statement_vals['recipient_name'] = employee.name
            serial_number += 1

            statement_vals_list.append(statement_vals)
        
        # 批次創建申報表紀錄
        if statement_vals_list:
            self.env['payslip.withholding.statement'].create(statement_vals_list)
        
        return True

    def _get_field_mapping(self):
        """回傳申報表欄位映射"""
        return [
            ('city_agency', '縣市機關別'),
            ('serial_number', '序號'),
            ('reporting_unit_tax_id', '申報單位統一編號'),
            ('income_note', '所得註記'),
            ('income_format', '所得格式'),
            ('recipient_tax_id', '所得人統編'),
            ('id_type', '證號別'),
            ('payable_add_subtotal', '給付總額'),
            ('withholding_tax', '扣繳稅額'),
            ('net_payment', '實付金額'),
            ('tax_credit_ratio', '稅額扣抵比率%'),
            ('allocation_count', '分配次數'),
            ('ex_dividend_date', '除權(息)基準-年月日'),
            ('software_note', '軟體註記'),
            ('error_note', '錯誤註記'),
            ('payment_year', '所得給付年度'),
            ('recipient_name', '所得人姓名'),
            ('recipient_address', '所得人地址'),
            ('income_period', '所得所屬期間'),
            ('self_retire', '自提勞退'),
            ('capital_reserve_cash_dividend', '資本公積現金股利'),
            ('stock_dividend', '股票股利'),
            ('stock_dividend_shares', '股票股利股數'),
            ('blank', '空白'),
            ('tax_credit_note', '扣抵稅額註記'),
            ('statement_issue_method', '憑單填發方式'),
            ('is_over_183_days', '是否滿183天'),
            ('residence_country_code', '居住地國或地區代碼'),
            ('tax_treaty_code', '租稅協定代碼'),
            ('blank2', '空白'),
            ('liquidation_date', '檔案製作日期'),
            ('tax_identification_number', '稅務識別碼'),
        ]

    def _get_statement_data(self, statement):
        """取得單一申報表記錄的資料"""
        data = []
        for field_name, field_label in self._get_field_mapping():
            value = getattr(statement, field_name, '')
            data.append(value or '')
        return data

    def download_excel(self):
        """下載Excel格式的申報資料"""
        import io
        import xlsxwriter
        
        # 準備Excel檔案
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        worksheet = workbook.add_worksheet('薪資代扣申報表')
        
        # 設定樣式
        header_format = workbook.add_format({
            'bold': True,
            'bg_color': '#D7E4BC',
            'border': 1,
            'align': 'center',
            'valign': 'vcenter'
        })
        data_format = workbook.add_format({
            'border': 1,
            'align': 'left',
            'valign': 'vcenter'
        })
        
        # 取得欄位映射
        field_mapping = self._get_field_mapping()
        headers = [field_label for field_name, field_label in field_mapping]
        
        # 寫入表頭
        for col, header in enumerate(headers):
            worksheet.write(0, col, header, header_format)
            worksheet.set_column(col, col, 15)
        
        # 寫入資料
        for row, statement in enumerate(self.statement_ids, 1):
            data = self._get_statement_data(statement)
            for col, value in enumerate(data):
                worksheet.write(row, col, value, data_format)
        
        workbook.close()
        output.seek(0)
        excel_data = base64.b64encode(output.getvalue())
        
        # 建立附件
        filename = f'{self.name}_申報資料.xlsx'
        attachment = self.env['ir.attachment'].create({
            'name': filename,
            'type': 'binary',
            'datas': excel_data,
            'res_model': self._name,
            'res_id': self.id,
            'mimetype': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        })
        
        return {
            'type': 'ir.actions.act_url',
            'url': f'/web/content/{attachment.id}?download=true',
            'target': 'self',
        }

    def download_csv(self):
        """下載CSV格式的申報資料"""
        import csv
        import io
        
        output = io.StringIO()
        writer = csv.writer(output)
        
        # 取得欄位映射和標題
        field_mapping = self._get_field_mapping()
        headers = [field_label for field_name, field_label in field_mapping]
        # writer.writerow(headers)
        
        # 寫入資料
        for statement in self.statement_ids:
            data = self._get_statement_data(statement)
            writer.writerow(data)
        
        output.seek(0)
        csv_data = base64.b64encode(output.getvalue().encode('utf-8-sig'))
        
        # 建立附件
        filename = f'{self.name}_申報資料.csv'
        attachment = self.env['ir.attachment'].create({
            'name': filename,
            'type': 'binary',
            'datas': csv_data,
            'res_model': self._name,
            'res_id': self.id,
            'mimetype': 'text/csv',
        })
        
        return {
            'type': 'ir.actions.act_url',
            'url': f'/web/content/{attachment.id}?download=true',
            'target': 'self',
        }

    def download_txt(self):
        """下載TXT格式的申報資料"""
        import csv
        import io
        
        output = io.StringIO()
        writer = csv.writer(output, delimiter='\t')  # 使用Tab分隔
        
        # 取得欄位映射和標題
        field_mapping = self._get_field_mapping()
        headers = [field_label for field_name, field_label in field_mapping]
        # writer.writerow(headers)
        
        # 寫入資料
        for statement in self.statement_ids:
            data = self._get_statement_data(statement)
            writer.writerow(data)
        
        output.seek(0)
        txt_data = base64.b64encode(output.getvalue().encode('utf-8-sig'))
        
        # 建立附件
        filename = f'{self.name}_申報資料.txt'
        attachment = self.env['ir.attachment'].create({
            'name': filename,
            'type': 'binary',
            'datas': txt_data,
            'res_model': self._name,
            'res_id': self.id,
            'mimetype': 'text/plain',
        })
        
        return {
            'type': 'ir.actions.act_url',
            'url': f'/web/content/{attachment.id}?download=true',
            'target': 'self',
        }
            
class PayslipWithholdingStatement(models.Model):
    _name = 'payslip.withholding.statement'
    _description = '薪資代扣申報表'
    
    statement_sheet_id = fields.Many2one(
        'payslip.withholding.statement.sheet',
        string='薪資代扣申報總表',
        required=True
    )
    
    employee_id = fields.Many2one(comodel_name='hr.employee', string='員工', required=True)
   
    city_agency = fields.Char(string="縣市機關別")
    serial_number = fields.Char(string="序號")
    reporting_unit_tax_id = fields.Char(string="申報單位統一編號")
    income_note = fields.Char(string="所得註記")
    income_format = fields.Char(string="所得格式")
    payable_add_subtotal = fields.Char(string="扣繳憑單給付總額")
    withholding_tax = fields.Char(string="扣繳憑單扣繳稅額")
    net_payment = fields.Char(string="扣繳憑單給付淨額")
    recipient_tax_id = fields.Char(string="所得人統編")
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
    self_retire = fields.Char(string="自提勞退")
    capital_reserve_cash_dividend = fields.Char(string="資本公積現金股利")
    stock_dividend = fields.Char(string="股票股利")
    stock_dividend_shares = fields.Char(string="股票股利股數")
    tax_credit_note = fields.Char(string="扣抵稅額註記")
    statement_issue_method = fields.Char(string="憑單填發方式")
    is_over_183_days = fields.Char(string="是否滿183天")
    residence_country_code = fields.Char(string="居住地國或地區代碼")
    tax_treaty_code = fields.Char(string="租稅協定代碼")
    liquidation_date = fields.Char(string="檔案製作日期")
    tax_identification_number = fields.Char(string="稅務識別碼")
    blank = fields.Char(string="空白")
    blank2 = fields.Char(string="空白")
    