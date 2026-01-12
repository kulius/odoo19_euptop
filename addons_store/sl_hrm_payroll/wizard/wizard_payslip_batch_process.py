from odoo import _, fields, models
from odoo.exceptions import UserError


class HrPayslipBatchProcessing(models.TransientModel):
    _name = "hr.payslip.batch.processing"
    _description = "批次生成薪資單"

    employee_ids = fields.Many2many(
        "hr.employee", "hr_employee_payslip_batch_processing", "payslip_id", "employee_id", "Employees"
    )

    hr_payroll_structure_id = fields.Many2one('hr.payroll.structure', string='薪資結構')

    def get_payroll_structure_employee(self):
        self.compute_sheet(self.env['hr.employee'].sudo().search([('struct_id', '=', self.hr_payroll_structure_id.id)]))

    def compute_sheet(self, structure_employee=False):
        payslips = self.env['hr.payslip']
        [data] = self.read()
        active_id = self.env.context.get('active_id')
        # 抓出薪資單批次處理的資料
        if active_id:
            [run_data] = self.env['hr.payslip.run'].browse(active_id).read(
                ['date_start', 'date_end', 'attendance_date_start', 'attendance_date_end', 'credit_note', 'is_payslip',
                 'is_unfrequented', 'tax_allocation_year', 'tax_allocation_month', 'unfrequented_ids'])
        from_date = run_data.get('date_start')
        to_date = run_data.get('date_end')
        attendance_from_date = run_data.get('attendance_date_start')
        attendance_to_date = run_data.get('attendance_date_end')
        is_payslip = run_data.get('is_payslip')
        is_unfrequented = run_data.get('is_unfrequented')
        tax_allocation_year = run_data.get('tax_allocation_year')
        tax_allocation_month = int(run_data.get('tax_allocation_month'))
        # struct_id = run_data.get("struct_id")
        # unfrequented_ids = run_data.get('unfrequented_ids')
        if structure_employee:
            all_employee = structure_employee
        else:
            # 檢查是否有選擇員工
            if not data['employee_ids']:
                raise UserError(_("您必須選擇員工以生成薪資單。"))
            else:
                all_employee = self.env['hr.employee'].browse(data['employee_ids'])

        # 產生每個員工的薪資單，沒有薪資資料的空單，會在payslips.compute_sheet()中產生薪資規則內的薪資資料
        for employee in all_employee:
            # slip_data = self.env["hr.payslip"].get_payslip_vals(attendance_from_date, attendance_to_date, employee.id)
            # # 抓出時薪人員當月的總工作時數
            # unfre_List = self.env['hr.payslip.unfrequented'].search(['&', ('employee_id', '=', employee.id),
            #                                                          '&', ('code', '=', 'BASIC'),
            #                                                          '&', ('gain_date', '>=', from_date),
            #                                                          ('gain_date', '<=', to_date)])
            #
            # hour = 0
            # for line in unfre_List:
            #     hour += line.part_time

            # if employee.contract_id.structure_type_id.name != 'Worker':
            #     hour_pay = 0
            # else:
            #     hour_pay = employee.contract_id.wage
            res = {
                'employee_id': employee.id,
                # 'name': slip_data['value'].get('name'),
                'struct_id': employee.struct_id.id,
                'payslip_run_id': active_id,
                # 'input_line_ids': [(0, 0, x) for x in slip_data['value'].get('input_line_ids')],
                # 'worked_days_line_ids': [(0, 0, x) for x in slip_data['value'].get('worked_days_line_ids')],
                # 'overtime_ids': [(0, 0, x) for x in slip_data['value'].get('overtime_ids')],
                'date_from': from_date,
                'date_to': to_date,
                'attendance_date_from': attendance_from_date,
                'attendance_date_to': attendance_to_date,
                'credit_note': run_data.get('credit_note'),
                'company_id': employee.company_id.id,
                'is_payslip': is_payslip,
                'is_unfrequented': is_unfrequented,
                # 'job_josition': job_josition if job_josition else '',
                # 'hour_pay': hour_pay if hour_pay else 0,
                # 'department_id': employee.department_id.name,
                # 'hour': hour,
                # 'date1_from': from_date1,
                # 'date1_to': to_date1,
                'tax_allocation_year': tax_allocation_year,
                'tax_allocation_month': str(tax_allocation_month),
            }
            payslips += self.env['hr.payslip'].create(res)
        # if is_unfrequented:

        # payslips._compute_name()
        payslips.compute_sheet()
        return {'type': 'ir.actions.act_window_close'}

