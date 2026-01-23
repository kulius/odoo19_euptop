from datetime import datetime, date

from odoo import models, api, fields
from odoo.exceptions import UserError
import logging

from dateutil.relativedelta import relativedelta


class StarryLordPayrollAdjustment(models.Model):
    _name = 'sl.payroll.adjustment'
    _description = '薪資手動調整紀錄'
    _rec_name = 'display_name'
    _order = 'payroll_allocation_date desc, employee_id'

    employee_id = fields.Many2one('hr.employee.public', string='員工', required=True)
    
    company_id = fields.Many2one(
        'res.company',
        string='公司',
        required=True,
        default=lambda self: self.env.company
    )
    
    payroll_allocation_date = fields.Date(string='認列日期', required=True, default=fields.Date.today)
    
    # 薪資規則選擇 - 用於界面操作
    salary_rule_id = fields.Many2one(
        'hr.salary.rule',
        string='薪資規則',
        help='選擇薪資規則，系統會自動填入代碼和分類',
        domain="[('company_id', 'in', [company_id])]",
        required=True,
    )
    
    # 規則分類相關欄位 - 自動從薪資規則帶入
    rule_category = fields.Char(string='規則分類', 
        related="salary_rule_id.category_id.name",
        help='例如：應稅加項、免稅加項、扣除項等')
    
    amount = fields.Float(string='金額', required=True)
    note = fields.Char(string='備註')
    exec_status = fields.Char(string='執行狀態', help='調整項目的執行狀態，例如：待處理、已處理、錯誤等', default='待處理')

    # 關聯薪資單 - 薪資計算時才會填入
    payslip_id = fields.Many2one('hr.payslip', string='關聯薪資單', readonly=True, help='此調整項目套用到的薪資單')
    payslip_sheet_id = fields.Many2one('hr.payslip.sheet', string='關聯薪資總表', readonly=True, help='此調整項目套用到的薪資總表')

    @api.model
    def copy_data(self, default=None):
        """複製時重置特定欄位"""
        if default is None:
            default = {}
        
        # 重置執行狀態和關聯欄位
        default.update({
            'exec_status': '待處理',
            'payslip_id': False,
            'payslip_sheet_id': False,
        })
        
        return super().copy_data(default)

    def mark_as_applied(self, status, payslip_sheet = False, payslip_id = False):
        """標記為已套用（由薪資計算系統呼叫）"""
        if status == 'success':
            self.write({
                'exec_status': '已處理',
                'payslip_sheet_id': payslip_sheet.id,
                'payslip_id': payslip_id.id
            })
        else : 
            self.write({
                'exec_status': '錯誤',
            })

    def get_adjustments_for_payslip(self, date_from, date_to):
        """取得指定員工、日期範圍和薪資代碼的調整項目（供薪資計算使用）"""
        domain = [
            ('payroll_allocation_date', '>=', date_from),
            ('payroll_allocation_date', '<=', date_to),
        ]
        return self.search(domain, order='employee_id')
    
class StarryLordPayslipSheetInheritAdjustment(models.Model):
    _inherit = "sl.hr.payslip.sheet"

    # 薪資調整計算 - 通用方法
    def payroll_adjustment(self):
        """計算指定薪資代碼的調整金額"""
        adjustments = self.env['sl.payroll.adjustment'].get_adjustments_for_payslip(
            self.date_from, self.date_to
        )
        success_count = 0
        for adjustment in adjustments:
            try:
                payslip_sheet = self
                payslip_id = self.payslip_ids.filtered(
                    lambda p: p.employee_id.id == adjustment.employee_id.id
                )
                if not payslip_id:
                    payroll_structure_id = self.env['hr.payroll.structure'].search([
                        ('company_id', '=', adjustment.company_id.id),
                    ], limit=1)
                    payslip_id = self.env['hr.payslip'].create({
                        'employee_id': adjustment.employee_id.id,
                        'date_from': self.date_from,
                        'date_to': self.date_to,
                        'sl_hr_payslip_sheet_id': self.id,
                        'payroll_structure_id': payroll_structure_id.id,
                    })
                payslip_line = payslip_id.payslip_line_ids.filtered(
                    lambda l: l.salary_rule_id.code == adjustment.salary_rule_id.code
                )
                if payslip_line:
                    if payslip_line.salary_rule_id.amount_select == 'code':
                        payslip_line.manual = True
                    payslip_line.amount = adjustment.amount
                    payslip_line.note = adjustment.note
                    payslip_line.manual = True
                else :
                    # 如果不存在對應項目，創建新的薪資單項目
                    salary_rule = self.env['hr.salary.rule'].search([
                        ('code', '=', adjustment.salary_rule_id.code),
                        ('company_id', '=', adjustment.company_id.id)
                    ], limit=1)
                    
                    if salary_rule:
                        manual = True if salary_rule.amount_select == 'code' else False
                        self.env['hr.payslip.line'].create({
                            'payslip_id': payslip_id.id,
                            'employee_id': adjustment.employee_id.id,
                            'salary_rule_id': salary_rule.id,
                            'amount': adjustment.amount,
                            'category_id': salary_rule.category_id.id,
                            'sequence': salary_rule.sequence,
                            'name': salary_rule.name,
                            'code': salary_rule.code,
                            'manual': manual,
                        })
                success_count += 1
                adjustment.mark_as_applied('success', payslip_sheet, payslip_id)
            except Exception as e:
                logging.error(f"薪資調整套用失敗：{str(e)}")
                adjustment.mark_as_applied('error')
        return {
            'message': f'已成功套用 {success_count} 條調整項目到薪資單',
        }

    def view_payroll_adjustment(self):
        return {
            'name': '檢視薪資調整紀錄',
            'view_type': 'tree',
            'view_mode': 'tree',
            'res_model': 'sl.payroll.adjustment',
            'view_id': False,
            'type': 'ir.actions.act_window',
            'target': 'new',
            'domain': [
                ('payroll_allocation_date', '>=', self.date_from),
                ('payroll_allocation_date', '<=', self.date_to)
            ]
        }