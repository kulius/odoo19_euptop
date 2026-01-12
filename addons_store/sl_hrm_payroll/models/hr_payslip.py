import base64
import io
from PyPDF2 import PdfWriter, PdfReader
from dateutil.relativedelta import relativedelta
from datetime import date, datetime, time, timedelta
from odoo import api, fields, models, _
import math

from odoo.exceptions import UserError


class BaseBrowsableObject(object):
    def __init__(self, vals_dict):
        self.__dict__["base_fields"] = ["base_fields", "dict"]
        self.dict = vals_dict

    def __getattr__(self, attr):
        return attr in self.dict and self.dict.__getitem__(attr) or 0.0

    def __setattr__(self, attr, value):
        _fields = self.__dict__["base_fields"]
        if attr in _fields:
            return super().__setattr__(attr, value)
        self.__dict__["dict"][attr] = value

    def __str__(self):
        return str(self.__dict__)


# These classes are used in the _get_payslip_lines() method
class BrowsableObject(BaseBrowsableObject):
    def __init__(self, employee_id, vals_dict, env):
        super().__init__(vals_dict)
        self.base_fields += ["employee_id", "env"]
        self.employee_id = employee_id
        self.env = env


class Payslips(BrowsableObject):
    """a class that will be used into the python code, mainly for
    usability purposes"""

    def sum(self, code, from_date, to_date=None):
        if to_date is None:
            to_date = fields.Date.today()
        self.env.cr.execute(
            """SELECT sum(case when hp.credit_note = False then
            (pl.total) else (-pl.total) end)
                    FROM hr_payslip as hp, hr_payslip_line as pl
                    WHERE hp.employee_id = %s AND hp.state = 'done'
                    AND hp.date_from >= %s AND hp.date_to <= %s AND
                     hp.id = pl.slip_id AND pl.code = %s""",
            (self.employee_id, from_date, to_date, code),
        )
        res = self.env.cr.fetchone()
        return res and res[0] or 0.0

    def rule_parameter(self, code):
        return self.env["hr.rule.parameter"]._get_parameter_from_code(
            code, self.dict.date_to
        )


class HrPayslip(models.Model):
    _name = 'hr.payslip'
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _description = "薪資單"

    name = fields.Char(string='薪資單編號')
    payroll_structure_id = fields.Many2one(comodel_name='hr.payroll.structure', string='薪資結構', required=True, readonly=True)
    user_id = fields.Many2one(comodel_name='res.users', string='User', related='employee_id.user_id', store=True)
    employee_id = fields.Many2one(comodel_name='hr.employee', string='員工', required=True)
    employee_number = fields.Char(
        string='員工編號', 
        related='employee_id.employee_number', 
        store=True, 
        readonly=True
    )
    labor_insurance_salary = fields.Integer(string='勞保級距', required=True, default=False)
    health_insurance_salary = fields.Integer(string='健保級距', required=True, default=False)
    labor_harm_insurance_salary = fields.Integer(string='勞工職業災害保險級距', required=True, default=False)
    labor_pension_salary = fields.Integer(string='勞退薪資', default=False)

    sl_hr_payslip_sheet_id = fields.Many2one(comodel_name='sl.hr.payslip.sheet', string='薪資單總表', ondelete='restrict')

    # # 薪資起迄日期
    salary_date = fields.Date(
        string='薪資月份',
        compute='_compute_salary_dates',
        store=True
    )
    date_from = fields.Date(
        string='薪資計算日期-起',
        # compute='_compute_salary_dates',
        store=True
    )
    date_to = fields.Date(
        string='薪資計算日期-迄',
        # compute='_compute_salary_dates',
        store=True
    )
    attendance_date_from = fields.Date(
        string="考勤起始日期",
        default=lambda self: fields.Date.today().replace(day=1),
    )
    attendance_date_to = fields.Date(
        string="考勤結束日期",
        default=lambda self: fields.Date.today().replace(day=1) + relativedelta(months=+1, day=1, days=-1),
    )
    state = fields.Selection(selection=[
        ('draft', '草稿'),
        ('confirm', '確認'),
        ('cancel', '取消'),
    ], string='狀態', default='draft', track=True, help="""* 創建薪資單時，狀態為 \'草稿\'
        \n* 如果薪資單已確認，則狀態設置為 \'完成\'.""")
    actual_pay_day = fields.Date(string='實際發放日', required=True, default=lambda self: fields.Date.today())
    overtime_ids = fields.One2many(comodel_name='starrylord.payslip.overtime.middleware', inverse_name='payslip_id', string='加班明細')
    holiday_ids = fields.One2many(comodel_name='starrylord.payslip.holiday.middleware', inverse_name='payslip_id', string='請假明細')
    overtime_holiday_ids = fields.One2many(comodel_name='starrylord.payslip.overtime.holiday.middleware', inverse_name='payslip_id', string='加班補休明細')
    payslip_line_ids = fields.One2many(comodel_name='hr.payslip.line', inverse_name='payslip_id', string='薪資明細')
    payslip_line_other_ids = fields.One2many(comodel_name='hr.payslip.other.line', inverse_name='payslip_id', string='他項薪資明細')
    employee_payslip_salary_setting_ids = fields.One2many(comodel_name="starrylord.employee.payslip.salary.setting"
                                                          , inverse_name='hr_payslip_id',
                                                          string='本薪變化')

    basic_wage = fields.Integer(string="底薪", store=False, compute='compute_taxable_add_subtotal', default=0)
    payable_add_subtotal = fields.Integer(string="應付總額", compute='compute_taxable_add_subtotal', store=False,
                                          default=0)
    deduction_subtotal = fields.Integer(string="代扣總額", compute='compute_taxable_add_subtotal', store=False,
                                        default=0)
    taxable_add_subtotal = fields.Integer(string="應稅加項小計", compute='compute_taxable_add_subtotal')
    taxable_decrease_subtotal = fields.Integer(string="應稅減項小計", compute='compute_taxable_add_subtotal')
    taxfree_add_subtotal = fields.Integer(string="免稅加項小計", compute='compute_taxable_add_subtotal')
    taxfree_decrease_subtotal = fields.Integer(string="免稅減項小計", compute='compute_taxable_add_subtotal')
    all_subtotal = fields.Integer(string="實發金額", compute='compute_taxable_add_subtotal')
    company_cost = fields.Integer(string="公司負擔", compute='compute_taxable_add_subtotal')
    over_tax_amount = fields.Integer(string='扣繳5%超過金額', default=0)
    second_health_fee_state = fields.Boolean(string='代扣二代健保費')
    second_health_payslip_line_ids = fields.One2many(comodel_name='hr.payslip.line',
                                                     inverse_name='second_health_payslip_id')
    payroll_report_attachment_ids = fields.Many2many(comodel_name='ir.attachment', string='薪資PDF檔案', relation="m2m_ir_payroll_report_rel",
                                                     column1="m2m_id",
                                                     column2="attachment_id")
    is_payslip_sent = fields.Boolean(string='已發送', default=False, readonly=True)
    payslip_sent_date = fields.Date(string='發送日期', readonly=True)
    used_record_ids = fields.One2many(comodel_name='starrylord.holiday.used.record',
                                      inverse_name='payslip_id', string='休假使用紀錄')
    note = fields.Html(string='備註', default=lambda self: self._get_default_note())
    
    registration_date = fields.Date(
        string='到職日期',
        related='employee_id.registration_date',
        store=True,
        readonly=True
    )
    resignation_date = fields.Date(
        string='離職日期',
        related='employee_id.resignation_date',
        store=True,
        readonly=True
    )

    def unlink(self):
        if any(self.filtered(lambda payslip: payslip.state not in ("draft", "cancel"))):
            raise UserError(_("您不能刪除狀態為已確認的薪資單"))
        return super(HrPayslip, self).unlink()

    def _get_default_note(self):
        default_note = self.env['ir.config_parameter'].sudo().get_param('sl_hrm_payroll.payslip_default_note', default=False)
        # if not default_note:
        #     default_note = '備註：\n1.年底獎金統一結算二代健保(獎金-健保投保薪資x4倍)x0.0211\n2.離職要先扣掉二代健保'
        return default_note

    def get_holiday_overtime(self, employee, date_from, date_to):
        on_day_holiday = self.env['starrylord.holiday.used.record'].search(
            [('employee_id', '=', employee.id), ('holiday_apply_id.state', '=', 'agree'), ('holiday_day', '>=', date_from), ('holiday_day', '<=', date_to)])
        domain = [('employee_id', '=', employee.id), ('state', '=', 'agree'), ('start_day', '>=', date_from), ('start_day', '<=', date_to)]
        regular_holiday_exclude_payroll = self.env['ir.config_parameter'].sudo().get_param('sl_hrm_payroll.regular_holiday_exclude_payroll', default=False)
        if regular_holiday_exclude_payroll:
            domain.append(('overtime_type_id.date_type', 'not in', ['regular_holiday']))

        on_day_overtime_apply = self.env['starrylord.overtime.apply'].search(domain)
        holiday_add = []
        overtime_add = []
        overtime_holiday_add = []
        for holiday in on_day_holiday:
            holiday_add.append((0, 0, {'employee_id': holiday.employee_id.id, 'start_day': holiday.holiday_day,
                                       'holiday_total_time': holiday.hours,
                                       'holiday_type_id': holiday.holiday_allocation_id.holiday_type_id.id,
                                       'holiday_apply_id': holiday.holiday_apply_id.id}))

        for overtime_apply in on_day_overtime_apply:
            # 如果假別是補休holiday, 剩餘時數必須大於0
            if overtime_apply.type == 'holiday':
                # 判斷加班補休時數仍大於0
                sl_holiday_allocation_ids = overtime_apply.sl_holiday_allocation_ids
                overtime_allocation_ids = sl_holiday_allocation_ids.filtered(lambda x: x.last_time > 0)
                if not overtime_allocation_ids:
                    continue
                for overtime_allocation in overtime_allocation_ids:
                    overtime_holiday_add.append({'employee_id': overtime_apply.employee_id.id, 'date_from': overtime_apply.start_day,
                                                 'distribute_time': overtime_allocation.distribute_time,
                                                 'days_no_tmp': overtime_allocation.last_time,
                                                 # 'rate': overtime_allocation.rate,
                                                 'allocation_id': overtime_allocation.id,
                                                 'overtime_type_id': overtime_apply.overtime_type_id.id,
                                                 'overtime_apply_id': overtime_apply.id})
            else:
                overtime_add.append((0, 0, {'employee_id': overtime_apply.employee_id.id, 'date_from': overtime_apply.start_day,
                                            'days_no_tmp': overtime_apply.duration_time,
                                            'type': overtime_apply.type,
                                            'overtime_type_id': overtime_apply.overtime_type_id.id,
                                            'overtime_apply_id': overtime_apply.id}))
        return holiday_add, overtime_add

    def _sum_salary_rule_category(self, localdict, category, amount, recurring_mark = 'recurring'):
        
        if category.code in localdict["categories"].dict:
            localdict["categories"].dict[category.code] += amount
        else:
            localdict["categories"].dict[category.code] = amount
            
        # 分類中再細分是否是常態薪資，計算代扣的部分會要分開計算
        key = category.code + ' ' + recurring_mark
        if key in localdict["categories"].dict:
            localdict["categories"].dict[key] += amount
        else:
            localdict["categories"].dict[key] = amount

        return localdict
    
    def _get_payslip_lines(self, payslip_id):

        payslip = self.env["hr.payslip"].browse(payslip_id)
        # contracts = self.env["hr.contract"].browse(contract_ids)

        # we keep a dict with the result because a value can be overwritten by
        # another rule with the same code
        result_dict = {}
        rules_dict = {}
        # contract_dict = {}
        # blacklist = []
        categories = BrowsableObject(payslip.employee_id.id, {}, self.env)
        rules = BrowsableObject(payslip.employee_id.id, rules_dict, self.env)
        # current_contract = BrowsableObject(
        #     payslip.employee_id.id, contract_dict, self.env
        # )
        # 放置資料的容器dictionary(字典)，後面的python code跑safe_eval時所要用的變數都裝在裡面，甚至跑完的結果也會在裡面
        baselocaldict = payslip.get_baselocaldict(payslip)
        baselocaldict["categories"] = categories
        baselocaldict["rules"] = rules
        # baselocaldict["current_contract"] = current_contract

        # 取得薪資結構內的薪資規則
        structure_ids = payslip.payroll_structure_id.id
        if not structure_ids:
            structure_ids = payslip.employee_id.payroll_structure_id.id
            payslip.struct_id = payslip.employee_id.payroll_structure_id.id
        # 將薪資規則照序號排好
        rule_ids = (
            self.env["hr.payroll.structure"].browse(structure_ids).get_all_rules()
        )
        # 照序號順序計算薪資規則
        sorted_rule_ids = [id for id, sequence in sorted(rule_ids, key=lambda x: x[1])]
        sorted_rules = self.env["hr.salary.rule"].browse(sorted_rule_ids)

        times = 1  # 迴圈次數
        # 將員工資料加入localdict
        employee = payslip.employee_id
        localdict = dict(baselocaldict, employee=employee)

        # 處理非經常性薪資
        # for wage in res.payslip_line_ids.filtered(lambda x: x.category_id.code == 'Taxfree_Decrease'):
        #     res.taxfree_decrease_subtotal += wage.amount

        for rule in sorted_rules:
            key = rule.code + '-' + str(employee.name)
            result = self._compute_single_rule(rule, employee, localdict, payslip)
            result_dict[key] = result
            rules_dict[rule.code] = rule
        # 做成可新增一筆many2one的格式
        return list(result_dict.values())


    def _compute_single_rule(self, rule, employee, localdict, payslip):
        """計算單一薪資規則，返回結果"""
        note = ''
        payslip_employee_setting_id = False
        localdict['result'] = None
        localdict['result_qty'] = 1.0
        localdict['result_rate'] = 100
        sum_amount, qty, rate = 0, 1.0, 100.0
        original_date_from = payslip.date_from
        original_date_to = payslip.date_to
        date_from = payslip.date_from
        date_to = payslip.date_to
        date_from_month = date_from.month
        date_to_month = date_to.month
        count_date_to = date_to
        # 取出薪資與計算百分比
        amount, qty, rate, computed_name = rule._compute_rule(localdict)
        #     取得薪資結構內的薪資規則
        payslip_employee_setting = (self.env['starrylord.employee.payslip.setting'].
                                    search([('employee_id', '=', employee.id),
                                            ('salary_rule_id', '=', rule.id),
                                            ('start_date', '<=', count_date_to)],
                                        order="start_date desc", limit=1))
        if payslip_employee_setting:
            amount = payslip_employee_setting.salary_amount
            payslip_employee_setting_id = payslip_employee_setting.id

        if rule.amount_select == 'fix' and rule.is_basic:
            partial_month_ratio = payslip.computed_partial_month_ratio
            amount = payslip_employee_setting.salary_amount * partial_month_ratio
            amount = float(payslip.true_round(amount, 0))

        sum_amount += amount
        payslip.date_from = original_date_from
        payslip.date_to = original_date_to

        # set/overwrite the amount computed for this rule in the localdict
        tot_rule = sum_amount * qty * rate / 100.0
        localdict[rule.code] = tot_rule
        # sum the amount for its salary category
        recurring_mark = 'non_recurring' if rule.is_non_recurring else 'recurring'
        localdict = self._sum_salary_rule_category(localdict, rule.category_id, tot_rule, recurring_mark)
        infrequent = False

        if rule.code == 'Healthy_dependents':
            # 計算出有幾位眷屬
            note = '%s位' % (len(employee.dependents_ids))

        # 將薪資規則打包，裡面包含薪資、發放比率等該薪資規則的細項
        return {
            'salary_rule_id': rule.id,
            'name': rule.name,
            'code': rule.code,
            'category_id': rule.category_id.id,
            'sequence': rule.sequence,
            'amount': sum_amount,
            'note': note,
            # 'appears_on_payslip': rule.appears_on_payslip,
            # 'condition_select': rule.condition_select,
            # 'condition_python': rule.condition_python,
            # 'condition_range': rule.condition_range,
            # 'condition_range_min': rule.condition_range_min,
            # 'condition_range_max': rule.condition_range_max,
            # 'amount_select': rule.amount_select,
            # 'amount_fix': rule.amount_fix,
            # 'amount_python_compute': rule.amount_python_compute,
            # 'amount_percentage': rule.amount_percentage,
            # 'amount_percentage_base': rule.amount_percentage_base,
            # 'register_id': rule.register_id.id,
            'payslip_employee_setting_id': payslip_employee_setting_id,
            # 'employee_id': employee.id,
            # 'quantity': qty,
            # 'rate': rate,
            'infrequent': rule.is_non_recurring,
        }
        
    def _compute_single_rule_recalculate(self, rule, employee, localdict, payslip, payslip_line):
        """計算單一薪資規則，返回結果"""
        note = ''
        payslip_employee_setting_id = False
        localdict['result'] = None
        localdict['result_qty'] = 1.0
        localdict['result_rate'] = 100
        sum_amount, qty, rate = 0, 1.0, 100.0

        # 因為line中的rule在當初產薪資的時候就固定了
        # 可能是舊的，所以要重新取得最新的rule
        curr_salary_rule = self.env['hr.salary.rule'].search([('id', '=', rule.id)], limit=1)
        if curr_salary_rule:
            rule = curr_salary_rule  # 取代成最新規則

        date_to = payslip.date_to
        payslip_employee_setting = (self.env['starrylord.employee.payslip.setting'].
                                    search([('employee_id', '=', employee.id),
                                            ('salary_rule_id', '=', rule.id),
                                            ('start_date', '<=', date_to)],
                                        order="start_date desc", limit=1))
        if rule.amount_select == 'code':
            amount, qty, rate, computed_name = rule._compute_rule(localdict)
        elif payslip_line.amount != 0:
            # 如果已經設定了就直接套用
            amount = payslip_line.amount
        elif payslip_employee_setting:
            amount = payslip_employee_setting.salary_amount
            payslip_employee_setting_id = payslip_employee_setting.id   
        else:
            amount = payslip_line.amount
            
        if rule.amount_select == 'fix' and rule.is_basic:
            partial_month_ratio = payslip.computed_partial_month_ratio
            amount = payslip_employee_setting.salary_amount * partial_month_ratio
            amount = float(payslip.true_round(amount, 0))

        sum_amount += amount

        # 計算最終薪資規則數值
        tot_rule = sum_amount * qty * rate / 100.0
        localdict[rule.code] = tot_rule

        recurring_mark = 'non_recurring' if rule.is_non_recurring else 'recurring'
        localdict = self._sum_salary_rule_category(localdict, rule.category_id, tot_rule, recurring_mark)
        infrequent = False
        
        # 眷屬計算
        if rule.code == 'Healthy_dependents':
            note = '%s位' % (len(employee.dependents_ids))

        # 回傳結果
        return {
            'salary_rule_id': rule.id,
            'name': rule.name,
            'code': rule.code,
            'category_id': rule.category_id.id,
            'sequence': rule.sequence,
            'amount': sum_amount,
            'note': note,
            'payslip_employee_setting_id': payslip_employee_setting_id,
            'infrequent': rule.is_non_recurring,
        }
        
    def compute_sheet(self, payslip=False):
        # 如果有匯入薪資單資料為重新計算薪資單，是用於全員薪資單重新計算的
        payslip_sum = []
        payslip_sum_add = []
        if payslip:
            payslip.name = payslip.name if payslip.name else self.env["ir.sequence"].next_by_code("hr.payslip")
            # 清除原有的薪資資料
            # payslip.line_ids.unlink()
            payslip.holiday_ids.unlink()
            payslip.overtime_ids.unlink()
            payslip.overtime_holiday_ids.unlink()
            payslip.employee_payslip_salary_setting_ids.unlink()
            payslip.used_record_ids.unlink()

            # 保險級距
            self.set_labor_insurance_salary()
            self.set_health_insurance_salary()
            self.set_labor_harm_insurance_salary()
            payslip.labor_pension_salary = self.employee_id.labor_pension_gap_id.insurance_salary
            # 請休假/加班明細
            holiday_ids, overtime_ids = self.env["hr.payslip"].get_holiday_overtime(payslip.employee_id,
                                                                                    payslip.date_from,
                                                                                    payslip.date_to)

            basic_amount = self.env["hr.payslip"].get_basic_amount_change(payslip.employee_id, payslip.date_from,
                                                                          payslip.date_to,
                                                                          payslip.date_from,
                                                                          payslip.date_to)
            payslip.update({"holiday_ids": holiday_ids, "overtime_ids": overtime_ids,
                            "employee_payslip_salary_setting_ids": basic_amount})

            # 整理補休時數
            # 初始化结果字典
            overtime_summary_dict = {}
            on_day_overtime_holiday_apply = self.env['starrylord.overtime.apply'].search(
                [
                    ('employee_id', '=', payslip.employee_id.id),
                    ('state', '=', 'agree'),
                    ('start_day', '>=', payslip.date_from),
                    ('start_day', '<=', payslip.date_to),
                    '|',
                    # type = 'holiday' 必須 allocation_validity_end <= payslip.date_to
                    '&',
                    ('type', '=', 'holiday'),
                    ('sl_holiday_allocation_ids.validity_end', '<=', payslip.date_to),
                    # type = 'cash' 不檢查 allocation_validity_end
                    ('type', '=', 'cash'),
                ]
            ) 

            # 遍历加班申请列表并累加每个日期和employee_id的小时数
            for overtime_apply in on_day_overtime_holiday_apply:
                # overtime產生補休(starrylord.holiday.used.record)的使用紀錄, 換算成薪資
                # for overtime_holiday_middleware in payslip.overtime_holiday_ids:
                if overtime_apply.type == 'holiday':
                    use_record = self.env['starrylord.holiday.used.record'].create({
                        'employee_id': payslip.employee_id.id,
                        'payslip_id': payslip.id,
                        'holiday_day': payslip.date_to,
                        'holiday_allocation_id': overtime_apply.sl_holiday_allocation_ids[0].id,
                        'hours': overtime_apply.sl_holiday_allocation_ids[0].last_time,
                        'note': '換算加班費'
                    })
                # overtime_holiday_middleware.used_record_id = use_record.id
                # use_record.payslip_overtime_holiday_middleware_id = overtime_holiday_middleware.id
                overtime_date = overtime_apply.start_day.strftime('%Y-%m-%d')
                hours = sum(overtime_apply.sl_holiday_allocation_ids.mapped('distribute_time'))
                used_time = hours - sum(overtime_apply.sl_holiday_allocation_ids.mapped('last_time'))
                hours = 0
                if overtime_apply.type == 'holiday':
                    hours = sum(overtime_apply.sl_holiday_allocation_ids.mapped('distribute_time'))
                    used_time = hours - sum(overtime_apply.sl_holiday_allocation_ids.mapped('last_time'))
                else:
                    hours = overtime_apply.duration_time
                    used_time = 0
                if overtime_date in overtime_summary_dict:
                    overtime_summary_dict[overtime_date]['distribute_time'] += hours
                    overtime_summary_dict[overtime_date]['used_time'] += used_time
                else:
                    allocation_id = overtime_apply.sl_holiday_allocation_ids[0].id if overtime_apply.sl_holiday_allocation_ids else False
                    overtime_summary_dict[overtime_date] = {'distribute_time': hours, 'used_time': used_time,
                                                            'overtime_type_id': overtime_apply.overtime_type_id.id,
                                                            'allocation_id': allocation_id}
            overtime_summary_list = [{'date': overtime_date, 'distribute_time': info['distribute_time'], 'used_time': info['used_time'], 'overtime_type_id': info['overtime_type_id']} for overtime_date, info in overtime_summary_dict.items()]

            # 寫入starrylord.payslip.overtime.holiday.middleware
            for overtime_summary in overtime_summary_list:
                # 取得加班類型的時數費率規則
                overtime_type_id = self.env['starrylord.overtime.type'].browse([overtime_summary['overtime_type_id']])
                overtime_rule_list = [{rule_id.time: rule_id.rate} for rule_id in overtime_type_id.rule_ids]
                # 初始化结果字典和起始点
                intervals_dict = {}
                start = 1

                # 遍历给定的数值和费率来生成区间
                for item in overtime_rule_list:
                    number = next(iter(item))
                    rate = item[number]
                    end = number
                    intervals_dict[(start, end)] = {
                        'range': list(range(start, end + 1)),
                        'rate': rate,
                        'used_hours': 0  # 初始化每个区间的已用时间为0
                    }
                    start = end + 1
                total_hours_first = overtime_summary['used_time']
                remaining_hours = total_hours_first
                # 计算在各区间分配的时间和相应费用（第一次）
                for (start, end), info in intervals_dict.items():
                    if remaining_hours <= 0:
                        break
                    interval_hours = end - start + 1
                    if remaining_hours >= interval_hours:
                        allocated_hours = interval_hours
                    else:
                        allocated_hours = remaining_hours
                    remaining_hours -= allocated_hours
                    info['used_hours'] += allocated_hours  # 更新已用时间

                # 第二次计算新增的2小时
                additional_hours = overtime_summary['distribute_time'] - overtime_summary['used_time']
                remaining_hours = additional_hours
                total_cost_second = 0

                # 计算在各区间分配的时间和相应费用（第二次）
                for (start, end), info in intervals_dict.items():
                    if remaining_hours <= 0:
                        break
                    interval_hours = end - start + 1
                    available_hours = interval_hours - info['used_hours']  # 剩余可用时间
                    if remaining_hours >= available_hours:
                        allocated_hours = available_hours
                    else:
                        allocated_hours = remaining_hours
                    remaining_hours -= allocated_hours
                    info['used_hours'] += allocated_hours  # 更新已用时间
                    if allocated_hours > 0:
                        # 寫入薪資表的加班費明細
                        self.env['starrylord.payslip.overtime.holiday.middleware'].create({
                            'payslip_id': payslip.id,
                            'employee_id': payslip.employee_id.id,
                            'date_from': overtime_summary['date'],
                            'rate': info['rate'],
                            'overtime_type_id': overtime_summary['overtime_type_id'],
                            'days_no_tmp': allocated_hours,
                        })

            lines = [
                (0, 0, line)
                for line in self._get_payslip_lines(payslip.id)
            ]
            payslip.update({"payslip_line_ids": lines})
        else:
            for payslip in self:
                payslip.name = payslip.name if payslip.name else self.env["ir.sequence"].next_by_code("hr.payslip")
                # 清除原有的薪資資料
                payslip.payslip_line_ids.unlink()
                payslip.holiday_ids.unlink()
                payslip.overtime_ids.unlink()
                payslip.overtime_holiday_ids.unlink()
                payslip.employee_payslip_salary_setting_ids.unlink()
                payslip.used_record_ids.unlink()
                # 保險級距
                self.set_labor_insurance_salary()
                self.set_health_insurance_salary()
                self.set_labor_harm_insurance_salary()
                payslip.labor_pension_salary = self.employee_id.labor_pension_gap_id.insurance_salary
                holiday_ids, overtime_ids = self.env["hr.payslip"].get_holiday_overtime(payslip.employee_id,
                                                                                        payslip.date_from,
                                                                                        payslip.date_to)
                # 列出本薪的變化
                basic_amount = payslip.env["hr.payslip"].get_basic_amount_change(payslip.employee_id, payslip.date_from,
                                                                                 payslip.date_to,
                                                                                 payslip.date_from,
                                                                                 payslip.date_to)
                payslip.write({"holiday_ids": holiday_ids, "overtime_ids": overtime_ids,
                               "employee_payslip_salary_setting_ids": basic_amount})
                # 整理補休時數
                # 初始化结果字典
                overtime_summary_dict = {}
                on_day_overtime_holiday_apply = self.env['starrylord.overtime.apply'].search(
                    [
                        ('employee_id', '=', payslip.employee_id.id),
                        ('state', '=', 'agree'),
                        ('start_day', '>=', payslip.date_from),
                        ('start_day', '<=', payslip.date_to),
                        '|',
                        # type = 'holiday' 必須 allocation_validity_end <= payslip.date_to
                        '&',
                        ('type', '=', 'holiday'),
                        ('sl_holiday_allocation_ids.validity_end', '<=', payslip.date_to),
                        # type = 'cash' 不檢查 allocation_validity_end
                        ('type', '=', 'cash'),
                    ]
                ) 

                # 遍历加班申请列表并累加每个日期和employee_id的小时数
                for overtime_apply in on_day_overtime_holiday_apply:
                    # overtime產生補休(starrylord.holiday.used.record)的使用紀錄, 換算成薪資
                    # for overtime_holiday_middleware in payslip.overtime_holiday_ids:
                    if overtime_apply.type == 'holiday':
                        use_record = self.env['starrylord.holiday.used.record'].create({
                            'employee_id': payslip.employee_id.id,
                            'payslip_id': payslip.id,
                            'holiday_day': payslip.date_to,
                            'holiday_allocation_id': overtime_apply.sl_holiday_allocation_ids[0].id,
                            'hours': overtime_apply.sl_holiday_allocation_ids[0].last_time,
                            'note': '換算加班費'
                        })
                    # overtime_holiday_middleware.used_record_id = use_record.id
                    # use_record.payslip_overtime_holiday_middleware_id = overtime_holiday_middleware.id
                    overtime_date = overtime_apply.start_day.strftime('%Y-%m-%d')
                    hours = 0
                    if overtime_apply.type == 'holiday':
                        hours = sum(overtime_apply.sl_holiday_allocation_ids.mapped('distribute_time'))
                        used_time = hours - sum(overtime_apply.sl_holiday_allocation_ids.mapped('last_time'))
                    else:
                        hours = overtime_apply.duration_time
                        used_time = 0
                    if overtime_date in overtime_summary_dict:
                        overtime_summary_dict[overtime_date]['distribute_time'] += hours
                        overtime_summary_dict[overtime_date]['used_time'] += used_time
                    else:
                        allocation_id = overtime_apply.sl_holiday_allocation_ids[0].id if overtime_apply.sl_holiday_allocation_ids else False
                        overtime_summary_dict[overtime_date] = {'distribute_time': hours, 'used_time': used_time,
                                                                'overtime_type_id': overtime_apply.overtime_type_id.id,
                                                                'allocation_id': allocation_id}
                overtime_summary_list = [{'date': overtime_date, 'distribute_time': info['distribute_time'], 'used_time': info['used_time'],
                                          'overtime_type_id': info['overtime_type_id']} for overtime_date, info in overtime_summary_dict.items()]
                # 寫入starrylord.payslip.overtime.holiday.middleware
                for overtime_summary in overtime_summary_list:
                    # 取得加班類型的時數費率規則
                    overtime_type_id = self.env['starrylord.overtime.type'].browse([overtime_summary['overtime_type_id']])
                    overtime_rule_list = [{rule_id.time: rule_id.rate} for rule_id in overtime_type_id.rule_ids]
                    # 初始化结果字典和起始点
                    intervals_dict = {}
                    start = 1

                    # 遍历给定的数值和费率来生成区间
                    for item in overtime_rule_list:
                        number = next(iter(item))
                        rate = item[number]
                        end = number
                        intervals_dict[(start, end)] = {
                            'range': list(range(start, end + 1)),
                            'rate': rate,
                            'used_hours': 0  # 初始化每个区间的已用时间为0
                        }
                        start = end + 1
                    total_hours_first = overtime_summary['used_time']
                    remaining_hours = total_hours_first
                    # 计算在各区间分配的时间和相应费用（第一次）
                    for (start, end), info in intervals_dict.items():
                        if remaining_hours <= 0:
                            break
                        interval_hours = end - start + 1
                        if remaining_hours >= interval_hours:
                            allocated_hours = interval_hours
                        else:
                            allocated_hours = remaining_hours
                        remaining_hours -= allocated_hours
                        info['used_hours'] += allocated_hours  # 更新已用时间
                    # 输出第一次总成本

                    # 第二次计算新增的2小时
                    additional_hours = overtime_summary['distribute_time'] - overtime_summary['used_time']
                    remaining_hours = additional_hours
                    total_cost_second = 0

                    # 计算在各区间分配的时间和相应费用（第二次）
                    for (start, end), info in intervals_dict.items():
                        if remaining_hours <= 0:
                            break
                        interval_hours = end - start + 1
                        available_hours = interval_hours - info['used_hours']  # 剩余可用时间
                        if remaining_hours >= available_hours:
                            allocated_hours = available_hours
                        else:
                            allocated_hours = remaining_hours
                        remaining_hours -= allocated_hours
                        info['used_hours'] += allocated_hours  # 更新已用时间
                        # 寫入薪資表的加班費明細
                        if allocated_hours > 0:
                            self.env['starrylord.payslip.overtime.holiday.middleware'].create({
                                'payslip_id': payslip.id,
                                'employee_id': payslip.employee_id.id,
                                'date_from': overtime_summary['date'],
                                'rate': info['rate'],
                                'overtime_type_id': overtime_summary['overtime_type_id'],
                                'days_no_tmp': allocated_hours,
                            })
                lines = [
                    (0, 0, line)
                    for line in self._get_payslip_lines(payslip.id)
                ]
                payslip.write({"payslip_line_ids": lines})
        return True
    @staticmethod
    def old_round(num, rounded=0):
        from decimal import Decimal, ROUND_HALF_UP
        """
         用於傳統意義的四捨五入的轉換.
        :參數 x: 浮點或字符串類型的帶轉換值
        :參數 rounded: 四捨五入的位數，當等於0時，返回一個int型返回值
        :return: 轉換後的浮點數
        """

        if rounded == 0:
            new_x = int(Decimal(str(num)).quantize(Decimal('0'), rounding=ROUND_HALF_UP))
        else:
            i = 0
            dec = '0.'
            while i < rounded:
                dec = dec + '0'
                i += 1
            new_x = float(Decimal(str(num)).quantize(Decimal(dec), rounding=ROUND_HALF_UP))
        return new_x

    def _init_payroll_dict_contracts(self):
        return {
            "count": 0,
        }

    def get_payroll_dict(self, contracts):
        """Setup miscellaneous dictionary values.
        Other modules may overload this method to inject discreet values into
        the salary rules. Such values will be available to the salary rule
        under the `payroll.` prefix.

        This method is evaluated once per payslip.
        :param contracts: Recordset of all hr.contract records in this payslip
        :return: a dictionary of discreet values and/or Browsable Objects
        """
        self.ensure_one()

        res = {
            # In salary rules refer to this as: payroll.contracts.count
            "contracts": BaseBrowsableObject(self._init_payroll_dict_contracts()),
        }
        res["contracts"].count = len(contracts)

        return res

    def get_baselocaldict(self, contracts):
        """Basic dictionary values that are useful in most salary rules. Inherited
        classes that overload this method should use the name of the module as
        the dictionary key.

        This method is evaluated once per payslip.

        :param contracts: Recordset of all hr.contract records in this payslip
        :return: a dictionary of discreet values and/or Browsable Objects
        """
        self.ensure_one()

        # worked_days_dict = {}
        # inputs_dict = {}
        payslip = self
        # for worked_days_line in payslip.worked_days_line_ids:
        #     worked_days_dict[worked_days_line.code] = worked_days_line
        # for input_line in payslip.input_line_ids:
        #     inputs_dict[input_line.code] = input_line
        # inputs = InputLine(payslip.employee_id.id, inputs_dict, self.env)
        # worked_days = WorkedDays(payslip.employee_id.id, worked_days_dict, self.env)
        payslips = Payslips(payslip.employee_id.id, payslip, self.env)
        payroll_dict = BrowsableObject(
            payslip.employee_id.id, payslip.get_payroll_dict(contracts), self.env
        )

        baselocaldict = {
            "payslip": payslips,
            # "worked_days": worked_days,
            # "inputs": inputs,
            "payroll": payroll_dict,
        }
        return baselocaldict

    def get_basic_amount_change(self, employee, date_from, date_to, attendance_date_from, attendance_date_to):
        setting = self.env['ir.config_parameter'].sudo()
        month_hour = float(setting.get_param('month_hour', default=False))  # 每月時數
        return_all_amount = []
        date_from = date_from if attendance_date_from > date_from else attendance_date_from
        date_to = date_to if attendance_date_to < date_to else attendance_date_to
        start_date_com = date_from
        start_date = date_from  # 薪資起算日
        end_date = date_to  # 薪資結算日
        all_amount_base = 0
        # 找出所有是本薪的薪資規則
        basic_rule_list = self.env['hr.salary.rule'].search([('is_basic', '=', True)])
        # 抓出本月之前本薪的狀況
        for basic_salary_rule in basic_rule_list:
            # 員工基本資料中, 找出是本薪的薪資規則最新一筆薪資設定
            last_basic_amount = self.env['starrylord.employee.payslip.setting'].search(
                [('employee_id', '=', employee.id), ('salary_rule_id', '=', basic_salary_rule.id),
                 ('start_date', '<=', date_from)], order="start_date desc", limit=1)
            # 將本月之前薪資規則的薪資存起來
            if last_basic_amount:
                all_amount_base += last_basic_amount.salary_amount
            # 沒有設定就為0
            else:
                all_amount_base += 0
        while start_date <= end_date:
            on_day_amount = 0
            change = self.env['starrylord.employee.payslip.setting'].search([('employee_id', '=', employee.id),
                                                                             ('is_basic_wage', '=', True),
                                                                             ('start_date', '=', start_date)])
            if change:
                for basic_salary_rule in basic_rule_list:
                    last_basic_amount = self.env['starrylord.employee.payslip.setting'].search(
                        [('employee_id', '=', employee.id), ('salary_rule_id', '=', basic_salary_rule.id),
                         ('start_date', '<', start_date)], order="start_date desc", limit=1)
                    # 將本月之前薪資規則的薪資存起來
                    if last_basic_amount:
                        on_day_amount += last_basic_amount.salary_amount
                if start_date != date_from:
                    return_all_amount.append((0, 0, {'start_date': start_date_com,
                                                     'end_date': start_date - timedelta(days=1),
                                                     'employee_id': employee.id, 'amount': on_day_amount,
                                                     'hour_amount': on_day_amount / month_hour}))
                    start_date_com = start_date
            start_date += timedelta(days=1)
        # 結束時最後的薪資，如果return_all_amount中有資料代表有異動，要補到最後的薪資
        if return_all_amount:
            on_day_amount = 0
            for basic_salary_rule in basic_rule_list:
                last_basic_amount = self.env['starrylord.employee.payslip.setting'].search(
                    [('employee_id', '=', employee.id), ('salary_rule_id', '=', basic_salary_rule.id),
                     ('start_date', '<', start_date)], order="start_date desc", limit=1)
                # 將本月之前薪資規則的薪資存起來
                if last_basic_amount:
                    on_day_amount += last_basic_amount.salary_amount
            return_all_amount.append((0, 0, {'start_date': start_date_com, 'end_date': date_to,
                                             'employee_id': employee.id, 'amount': on_day_amount,
                                             'hour_amount': on_day_amount / month_hour}))
        # return_all_amount沒有資料則代表沒有異動，直接加入未異動薪資
        else:
            return_all_amount.append((0, 0, {'start_date': date_from, 'end_date': date_to,
                                             'employee_id': employee.id, 'amount': all_amount_base,
                                             'hour_amount': all_amount_base / month_hour}))
        return return_all_amount

    # 請假扣薪計算
    def holiday(self, id, holiday_ids, base_wage_ids):
        all_wage = 0
        for holiday in holiday_ids:
            all_time = 0.0
            # 時薪
            wage = base_wage_ids.filtered(lambda x: x.start_date <= holiday.start_day <= x.end_date).hour_amount
            # 根據薪資類型的計算方式
            if holiday.holiday_type_id.salary_calculation == 'full_pay':  # 全薪計算
                pay_rate = 0
            elif holiday.holiday_type_id.salary_calculation == 'half_pay':  # 半薪計算
                pay_rate = 0.5
            else:
                pay_rate = 1
            all_time += holiday.holiday_total_time
            all_wage += wage * all_time * pay_rate
        all_wage = math.floor(all_wage * 10000) / 10000.0
        all_wage = self.old_round(all_wage)
        return all_wage
    
    def overtime(self, id, overtime_ids, overtime_holiday_ids, base_wage_ids):
        # employee_id = self.env['hr.employee'].browse(id)
        all_wage = 0
        # for overtime in overtime_ids:
        #     # 抓出時薪
        #     wage = base_wage_ids.filtered(lambda x: x.start_date <= overtime.date_from <= x.end_date).hour_amount
        #     # 假別為補假不支薪(補休時數每月結算加班費,歸0)
        #     # if overtime.type == 'holiday':
        #     #     wage = 0
        #     all_time = overtime.days_no_tmp
        #     all_rule = overtime.overtime_type_id.rule_ids
        #     for rule in all_rule:
        #         if overtime.overtime_type_id.eight_hours and all_time < 8:
        #             all_time = 8
        #             rate = rule.rate
        #             all_wage += all_time * rate * wage
        #             break
        #         if all_rule.ids.index(rule.id) != 0:
        #             past_time = all_rule[all_rule.ids.index(rule.id) - 1].time
        #         else:
        #             past_time = 0
        #         if overtime.days_no_tmp >= rule.time:
        #             rate = rule.rate
        #             all_wage += (rule.time - past_time) * rate * wage
        #         else:
        #             rate = rule.rate
        #             if past_time >= all_time:
        #                 break
        #             all_wage += (all_time - past_time) * rate * wage
        # 計算補休時數換算成加班費
        for overtime in overtime_holiday_ids:
            # 抓出時薪
            wage = base_wage_ids.filtered(lambda x: x.start_date <= overtime.date_from <= x.end_date).hour_amount
            all_wage += overtime.days_no_tmp * overtime.rate * wage
        all_wage = math.floor(all_wage * 10000) / 10000.0
        all_wage = self.old_round(all_wage)
        return all_wage

    # 勞保破月處理
    def labor_days(self, amount, employee, date_from, date_to, all_rate, percent, month_day=30):
        if not month_day:
            return 0
        all_amount1 = 0
        all_amount2 = 0
        # 計算所有的費率並加總

        # 如為全月投保級距則直接輸出投保級距，當amount為int時代表為全月投保級距
        if type(amount) == float or type(amount) == int:
            labor_accident_rate = all_rate[0]  # 普通事故費率
            labor_employment_rate = all_rate[1]  # 就業保險費率
            valid_data = self.env['hr.labor.insurance.history'].search(
                [('labor_insurance_history_id', '=', employee.id),
                 ('start_date', '<=', date_from)],
                order='start_date desc', limit=1)
            if valid_data.labor_identity == 'only_accident':  # 僅參加就業保險
                labor_accident_rate = 0
            elif valid_data.labor_identity == 'no_accident':
                labor_employment_rate = 0

            # 如果all_rate[2]是11，代表是公司勞保，不會有減免，所以將labor_rate設為1
            if all_rate[2] == 11:
                labor_rate = 1
            else:
                labor_rate = float(valid_data.labor_rate)
            all_amount1 += amount * labor_accident_rate * labor_rate * percent
            all_amount2 += amount * labor_employment_rate * labor_rate * percent
        else:
            for i in amount:
                labor_accident_rate = all_rate[0]  # 普通事故費率
                labor_employment_rate = all_rate[1]  # 就業保險費率
                # 如果all_rate[2]是11，代表是公司勞保，不會有減免，所以將labor_rate設為1
                if all_rate[2] == 11:
                    labor_rate = 1
                else:
                    labor_rate = i['labor_rate']
                if i['labor_identity'] == 'only_accident':
                    labor_accident_rate = 0
                elif i['labor_identity'] == 'no_accident':
                    labor_accident_rate = 0
                    labor_employment_rate = 0
                all_amount1 += i['wage'] * (i['part_day'] / month_day) * labor_accident_rate * labor_rate * percent
                all_amount2 += i['wage'] * (
                        i['part_day'] / month_day) * labor_employment_rate * labor_rate * percent
        # 無條件捨去到小數點後4位 round(amount + 0.1111)
        all_amount1 = math.floor(all_amount1 * 10000) / 10000.0
        all_amount2 = math.floor(all_amount2 * 10000) / 10000.0
        if employee.is_foreign:
            # 外籍勞工不計算就業保險費率
            all_amount2 = 0
        # 當月多段異動紀錄的計算是將普通事故費率與就業保險費率分開計算，最後各自加總後四捨五入最後在加起來
        all_amount = self.old_round(all_amount1) + self.old_round(all_amount2)
        return all_amount

    # 勞保
    def labor(self, id, hour_pay, hour, date_from, date_to, rule_code='Labor', count_type=0):
        employee_id = self.env['hr.employee'].browse(id)

        # 勞保異動紀錄
        insurance_history = self.env['hr.labor.insurance.history'].search([('labor_insurance_history_id', '=', id)],
                                                                          order='start_date')

        # 勞保薪資規則
        rule = self.env['hr.salary.rule'].search([
            ('code', '=', rule_code),
            ('company_id', '=', employee_id.company_id.id)
        ], limit=1)
        on_day_pay = insurance_history.filtered(lambda r: date_to >= r.start_date >= date_from)
        active_check = insurance_history.filtered(lambda r: date_to >= r.start_date)
        setting = self.env['ir.config_parameter'].sudo()
        labor_accident_rate = float(setting.get_param('labor_accident_rate', default=False)) / 100  # 普通事故費率
        labor_employment_rate = float(setting.get_param('labor_employment_rate', default=False)) / 100  # 就業保險費率
        first_day_of_month = date_from.replace(day=1)
        last_day_of_month = (first_day_of_month.replace(month=first_day_of_month.month % 12 + 1,
                                                        year=first_day_of_month.year + first_day_of_month.month // 12) - timedelta(days=1))

        first_day = first_day_of_month - date_from
        last_day = last_day_of_month - date_to
        # 無變更紀錄代表薪資為原樣，無須多段計算
        if not on_day_pay and not first_day and not last_day:
            if active_check:
                valid_history_data = insurance_history.filtered(lambda r: date_from >= r.start_date).sorted(
                    key='start_date',
                    reverse=True)[:1]
                day_pay = valid_history_data.labor_insurance_gap  # 勞保級距
                if valid_history_data.labor_identity == 'only_accident':
                    labor_accident_rate = 0
                elif valid_history_data.labor_identity == 'no_accident':
                    labor_employment_rate = 0
            else:
                day_pay = 0
        else:
            employee_id.is_payslip_compute = True  # 設定員工正在計算薪資
            # 勞保級距
            set_zero = self.env['hr.labor.insurance.gap'].sudo().search([('insurance_salary', '=', 0)],
                                                                        order="create_date desc", limit=1)
            set_zero.is_labor = True
            set_zero_id = set_zero.id
            change_data = []
            first_day_data = self.env['hr.labor.insurance.history']
            # 開始日非當月第一天
            if first_day:
                front = self.env['hr.labor.insurance.history'].search([('labor_insurance_history_id', '=', id),
                                                                       ('start_date', '<=', date_from)],
                                                                      order='start_date desc', limit=1)
                if front.start_date != date_from:
                    change_data.append({'start_date': front.start_date, 'id': front.id})
                    front.start_date = date_from
            # 結束日非當月最後一天
            if last_day:
                after = self.env['hr.labor.insurance.history'].search([('labor_insurance_history_id', '=', id),
                                                                       ('start_date', '>=', date_to)],
                                                                      order='start_date asc', limit=1)
                last_front = self.env['hr.labor.insurance.history'].search([('labor_insurance_history_id', '=', id),
                                                                            ('start_date', '<', date_to)],
                                                                           order='start_date desc', limit=1)
                # 當天結束點沒有異動資料，加入0代表停止點
                if after.start_date != date_to:
                    first_day_data += self.env['hr.labor.insurance.history'].sudo().create(
                        {'labor_insurance_history_id': id, 'start_date': date_to,
                         'labor_identity': 'normal', 'labor_rate': '1', 'labor_insurance_gap_id': set_zero_id,
                         'change_reason_selection': 'add' if last_front.change_reason_selection not in ['add', 'promote'] else 'off', })
                # 有資料但是是加保，將該筆資料移動到他日再進行停止點的加入
                elif after.change_reason_selection in ['add', 'promote']:
                    change_data.append({'start_date': after.start_date, 'id': after.id})
                    after.start_date = after.start_date + timedelta(days=2)
                    first_day_data += self.env['hr.labor.insurance.history'].sudo().create(
                        {'labor_insurance_history_id': id, 'start_date': date_to,
                         'labor_identity': 'normal', 'labor_rate': '1', 'labor_insurance_gap_id': set_zero_id,
                         'change_reason_selection': 'add' if last_front.change_reason_selection not in ['add', 'promote'] else 'off', })
                # 如果沒有增加前方的資料就要在這裡補上
                if not first_day:
                    front = self.env['hr.labor.insurance.history'].search([('labor_insurance_history_id', '=', id),
                                                                           ('start_date', '<=', date_from)],
                                                                          order='start_date desc', limit=1)
                    first_day_data += self.env['hr.labor.insurance.history'].sudo().create(
                        {'labor_insurance_history_id': front.labor_insurance_history_id.id, 'start_date': date_from,
                         'labor_identity': front.labor_identity, 'labor_rate': front.labor_rate,
                         'labor_insurance_gap_id': front.labor_insurance_gap_id.id,
                         'change_reason_selection': 'add' if front.change_reason_selection not in ['add', 'promote'] else 'off', })
            # 因為開始日非當月第一天或結束日非當月最後一天，因此強制只接收區間內的資料
            if first_day or last_day:
                insurance_history = self.env['hr.labor.insurance.history'].search(
                    [('labor_insurance_history_id', '=', id)], order='start_date')
                on_day_pay = insurance_history.filtered(lambda r: date_to >= r.start_date >= date_from)
                insurance_history = on_day_pay
            # 計算日薪
            day_pay = self.env['hr.payslip'].count_day_wage(insurance_history, on_day_pay, date_from, date_to,count_type)
            # 計算用的資料在使用完畢後全部清除、復原
            set_zero.is_labor = False
            employee_id.is_payslip_compute = False
            if first_day_data:
                first_day_data.unlink()
            for original in change_data:
                self.env['hr.labor.insurance.history'].search([('id', '=', original['id'])]).start_date = original[ 'start_date']
        all_rate = [labor_accident_rate, labor_employment_rate, count_type]
        # 單日薪水另外處理
        if date_from == date_to:
            front = self.env['hr.labor.insurance.history'].search([('labor_insurance_history_id', '=', id),
                                                                   ('start_date', '<=', date_from)],
                                                                  order='start_date desc', limit=1)
            day_pay = [{'wage': front.labor_insurance_id.insured_grade_distance, 'part_day': 1,
                        'labor_rate': float(front.labor_rate), 'labor_identity': front.labor_identity}]
        # 取得計算天數基數
        day = self.env['hr.payslip'].baseline(day_pay, rule, employee_id, date_from, date_to, True)
        # 判斷是否為公司負擔的勞保，10為勞保
        if count_type == 10:
            labor_insurer_pay = float(setting.get_param('labor_insurer_pay', default=False)) / 100  # 勞保保險人負擔比率
            all_amount = self.labor_days(day_pay, employee_id, date_from, date_to, all_rate, labor_insurer_pay, day)
        # 11為公司勞保
        elif count_type == 11:
            labor_insurer_pay = float(setting.get_param('labor_insurer_company_pay', default=False)) / 100  # 勞保投保單位負擔比率
            all_amount = self.env['hr.payslip'].labor_days(day_pay, employee_id, date_from, date_to, all_rate,
                                                           labor_insurer_pay, day)
        # 12是工資墊償
        elif count_type == 12:
            rate = float(setting.get_param('salary_advance_rate', default=False)) / 100  # 工資墊償費率
            if isinstance(day_pay, (int, float)):
                day_pay = day_pay * rate
            all_amount = self.env['hr.payslip'].labor_pension_days(day_pay, employee_id, date_from, date_to, rate,
                                                                   day)
        # 13是職業災害
        elif count_type == 13:
            rate = float(setting.get_param('work_accident_rate', default=False)) / 100  # 職業災害費率
            if isinstance(day_pay, (int, float)):
                day_pay = day_pay * rate
            all_amount = self.env['hr.payslip'].labor_pension_days(day_pay, employee_id, date_from, date_to, rate,
                                                                   day)
        else:
            all_amount = 0
        amount = self.old_round(all_amount)
        return amount

    # 計算在該薪資下的工作天數
    def count_day_wage(self, pay_data, on_day_pay, date_from, date_to, count_type=0):
        # 判斷是否為勞保、勞退或是薪水以此取值
        def get_wage(wage_data, wage_type):
            if wage_type == 0:  # 薪資設定
                res = wage_data.amount
            elif wage_type == 10 or wage_type == 11 or wage_type == 12 or wage_type == 13:  # 勞保
                res = wage_data.labor_insurance_gap
            elif wage_type == 20 or wage_type == 21:  # 勞退
                res = wage_data.labor_pension_salary
            else:
                res = 0
            return res

        # 取得政府補助勞保比例與是否參加就業保險，或是勞退自提比例
        def get_other(other_data, other_type):
            if other_type == 10 or other_type == 11:  # 勞保
                res = {'labor_rate': float(other_data.labor_rate), 'labor_identity': other_data.labor_identity}
            elif other_type == 21:  # 勞退自提
                res = {'self_labor_pension': float(other_data.self_reimbursement_of_labor_pension)}
            else:
                res = False
            return res

        use_check = False
        start_date = date_from.day
        day_pay = []
        for data in on_day_pay:
            # 用此確認該筆紀錄是否被使用過
            if use_check:
                use_check = False
                continue
            # 離職與留職停薪代表該日為終點，所以依照前一筆資料的日期計算薪水與工作日
            if data.change_reason_selection == 'resign' or data.change_reason_selection == 'furlough' or \
                    data.change_reason_selection == 'off':
                # 如果第一筆就是離職或留職停薪，起始時間就是該薪資單開始的時間
                if on_day_pay.ids.index(data.id) == 0:
                    wage = get_wage(pay_data[pay_data.ids.index(data.id) - 1], count_type)
                    other = get_other(pay_data[pay_data.ids.index(data.id) - 1], count_type)
                    end_date = data.start_date.day
                # 因並非第一筆，所以起始時間為上筆紀錄的生效日期，薪資也是上一筆紀錄的
                else:
                    wage = get_wage(on_day_pay[on_day_pay.ids.index(data.id) - 1], count_type)
                    other = get_other(on_day_pay[on_day_pay.ids.index(data.id) - 1], count_type)
                    start_date = on_day_pay[on_day_pay.ids.index(data.id) - 1].start_date.day
                    end_date = data.start_date.day
            else:
                # 剩餘的則是到職，復職薪資異動等
                try:
                    # 找出下筆紀錄的薪資與生效日期
                    next_data = on_day_pay[on_day_pay.ids.index(data.id) + 1]
                    past_data = pay_data[pay_data.ids.index(data.id) - 1]
                    # 確認是否為該月第一筆
                    if on_day_pay.ids.index(data.id) != 0:  # 不是第一筆
                        start_date = past_data.start_date.day
                        end_date = data.start_date.day
                        wage = get_wage(past_data, count_type)
                        other = get_other(past_data, count_type)
                    # 確認是否為該員工第一筆異動資料
                    elif pay_data.ids.index(data.id) == 0:
                        start_date = data.start_date.day
                        # 因為是第一筆起始的異動資料，需要使用下一筆異動資料做為終點
                        end_date = next_data.start_date.day
                        wage = get_wage(data, count_type)
                        other = get_other(data, count_type)
                        # 當下筆資料已經使用過將use_check變為True，使下筆資料不會進行計算
                        use_check = True
                        # 如果後一筆異動是本月最後一筆異動資料，便將前後部分都新增
                        if len(on_day_pay) - 1 == on_day_pay.ids.index(data.id) + 1:
                            # 將前半部分的薪資與工作日新增
                            part_day = end_date - start_date + 1
                            only_day_pay = {'wage': wage, 'part_day': part_day}
                            if other:
                                only_day_pay.update(other)
                            day_pay.append(only_day_pay)
                            # 再增加變更後的薪資與工作日
                            wage = get_wage(next_data, count_type)
                            other = get_other(next_data, count_type)
                            start_date = next_data.start_date.day
                            if count_type:
                                end_date = 30
                            else:
                                end_date = date_to.day
                    # 是該月第一筆但之前有異動資料
                    else:
                        start_date = date_from.day
                        end_date = data.start_date.day
                        wage = get_wage(past_data, count_type)
                        other = get_other(past_data, count_type)
                # 進入except代表找不到下筆紀錄，代表已執行到最後一筆異動資料或是只有一筆
                except:
                    # 先增加未變更前的薪資與工作日
                    past_data = pay_data[pay_data.ids.index(data.id) - 1]
                    wage = get_wage(past_data, count_type)
                    other = get_other(past_data, count_type)
                    # 不是該月第一筆
                    if on_day_pay.ids.index(data.id) != 0:
                        start_date = data.start_date.day
                    if past_data.start_date.month == date_from.month:
                        end_date = past_data.start_date.day
                    else:
                        end_date = data.start_date.day
                    if start_date > end_date:
                        part_day = start_date - end_date
                    else:
                        part_day = end_date - start_date
                    # 如果前一筆是離職、留職停薪、退保，代表此段時間並不在職，資料無須匯入進行計算，反之則需要加入
                    if past_data.change_reason_selection != 'resign' and past_data.change_reason_selection != 'furlough' \
                            and past_data.change_reason_selection != 'off':
                        only_day_pay = {'wage': wage, 'part_day': part_day}
                        if other:
                            only_day_pay.update(other)
                        if len(pay_data) != 1:
                            day_pay.append(only_day_pay)
                    # 再增加變更後的薪資與工作日
                    wage = get_wage(data, count_type)
                    other = get_other(data, count_type)
                    start_date = data.start_date.day
                    if count_type:
                        end_date = 30
                    else:
                        end_date = date_to.day
            # 計算工作日
            part_day = end_date - start_date + 1
            # 於最後一筆異動資料補入一天，如該筆為離職或留職停薪，因即日生效所以不補入當日進行計算
            # if (on_day_pay.ids.index(data.id) == len(on_day_pay) - 1 and
            #     (data.change_reason_selection != 'resign' and data.change_reason_selection != 'furlough')) or \
            #         count_type > 10:  # ( and data.change_reason_selection != 'off')
            #     part_day += 1
            # wage為薪水，part_day為工作日，代表在該薪水下工作的天數
            only_day_pay = {'wage': wage, 'part_day': part_day}
            if other:
                only_day_pay.update(other)
            day_pay.append(only_day_pay)
        return day_pay

    # 勞退破月處理
    def labor_pension_days(self, amount, employee, date_from, date_to, pension_rate=0.0, month_day=30):
        if not month_day:
            return 0
        all_amount = 0
        day_count = 0
        # 如為int代表無異動，直接輸出薪資
        if type(amount) == int or type(amount) == float:
            all_amount = amount
        else:
            for i in amount:
                # 如果pension_rate中有值代表為單一個勞退提繳比例，沒有代表是多段的勞退，會從amount中提取每次的勞退比例計算
                if pension_rate:
                    count_pension_rate = pension_rate
                else:
                    count_pension_rate = i['self_labor_pension']
                if day_count + i['part_day'] <= month_day:
                    day_count += i['part_day']
                else:
                    i['part_day'] = month_day - day_count
                all_amount += i['wage'] / month_day * i['part_day'] * count_pension_rate
        # 無條件捨去到小數點後4位
        all_amount = math.floor(all_amount * 10000) / 10000.0
        return all_amount

    def healthy(self, employee_id, date_from, date_to, rule_code='Healthy', is_comp=False):
        amount_end = False
        total_amount = 0
        employee = self.env['hr.employee'].browse(employee_id)
        rule = self.env['hr.salary.rule'].search([
            ('code', '=', rule_code),
            ('company_id', '=', employee.company_id.id)
        ], limit=1)
        # 健異動歷程
        pay_data = self.env['hr.health.insurance.history'].search([('health_insurance_history_id', '=', employee_id)],
                                                                  order='start_date')
        on_day_pay = pay_data.filtered(lambda r: date_to >= r.start_date >= date_from)
        active_check = pay_data.filtered(lambda r: date_to >= r.start_date)
        setting = self.env['ir.config_parameter'].sudo()
        health_rate = float(setting.get_param('health_rate', default=False)) / 100  # 健保費率
        health_insurer_pay = float(setting.get_param('health_insurer_pay', default=False)) / 100  # 健保保險人負擔比率
        health_insurer_company_pay = float(setting.get_param('health_insurer_company_pay', default=False)) / 100  # 健保投保單位負擔比率
        health_dependents_max = int(setting.get_param('health_dependents_max', default=False))  # 眷口數上限
        health_dependents_average = float(setting.get_param('health_dependents_average', default=False)) + 1  # 平均眷口數
        dependents_data = self.env['hr.dependents.information'].search([
            ('employee_id', '=', employee_id),
            ('add_insurance_time', '<=', date_to),
            '|',  # OR 運算
            ('cancel_insurance_time', '=', False),  # 為 NULL (Odoo 中 False 代表 NULL)
            ('cancel_insurance_time', '>=', date_to)  # 大於等於 date_to
        ], limit=health_dependents_max, order="health_rate")  # 健保眷屬明細，取前三個支付金額最少的眷屬
        first_day_of_month = date_from.replace(day=1)
        last_day_of_month = (first_day_of_month.replace(month=first_day_of_month.month % 12 + 1,
                                                        year=first_day_of_month.year + first_day_of_month.month // 12) - timedelta(days=1))

        last_day = last_day_of_month
        # 判斷離職時間點
        day = self.env['hr.payslip'].baseline(on_day_pay, rule, employee, date_from, date_to, True)
        is_legal_agent = False
        # 判斷是否為最後一筆
        # 確認當月有無變更級距，有則使用異動資料
        if on_day_pay:
            is_last_day = last_day_of_month - date_to
            insurance_history_data = on_day_pay[len(on_day_pay) - 1]
            wage = float(insurance_history_data.health_insurance_gap_id.insurance_salary)
            emp_health_rate_pay = float(insurance_history_data.health_insurance_gap_id.employee_pay)
            com_health_rate_pay = float(insurance_history_data.health_insurance_gap_id.company_pay)
            legal_health_rate_pay = float(insurance_history_data.health_insurance_gap_id.legal_pay)
            subsidy = float(insurance_history_data.health_rate)
            # 如最後一筆資料為退保，並且非最後一天退保，則當月不保
            if insurance_history_data.change_reason_selection == 'off':
                wage = float(pay_data[pay_data.ids.index(insurance_history_data.id) - 1].health_insurance_gap_id.insurance_salary)
                emp_health_rate_pay = 0
                com_health_rate_pay = 0
                legal_health_rate_pay = 0
            if insurance_history_data.change_reason_selection == 'off' and insurance_history_data.start_date < last_day or is_last_day:
                wage = 0
                emp_health_rate_pay = 0
                com_health_rate_pay = 0
                legal_health_rate_pay = 0
            if insurance_history_data.heath_rate_type == 'legal':
                is_legal_agent = True
        # 無變更直接使用明細資料
        else:
            is_last_day = last_day_of_month - date_to
            if active_check and not is_last_day:
                valid_data = pay_data.filtered(lambda r: date_from >= r.start_date).sorted(key='start_date', reverse=True)[:1]
                wage = float(valid_data.health_insurance_gap)
                emp_health_rate_pay = float(valid_data.health_insurance_gap_id.employee_pay)
                com_health_rate_pay = float(valid_data.health_insurance_gap_id.company_pay)
                legal_health_rate_pay = float(valid_data.health_insurance_gap_id.legal_pay)
                subsidy = float(valid_data.health_rate)
                if valid_data.heath_rate_type == 'legal':
                    is_legal_agent = True
            else:
                wage = 0
                subsidy = 0
                emp_health_rate_pay = 0
                com_health_rate_pay = 0
                legal_health_rate_pay = 0

        # 雇主身份 以雇主費率計算
        if is_legal_agent:
            amount = self.old_round(math.floor(legal_health_rate_pay * day * 10000) / 10000.0)
            # # 計算眷保
            # if dependents_data:
            #     for dependent in dependents_data:
            #         if dependent.cancel_insurance_time and dependent.cancel_insurance_time < last_day:
            #             total_amount += 0
            #         else:
            #             total_amount += self.old_round(amount * float(dependent.health_rate))
            total_amount += amount
        else:
            # 如計算公司負擔的健保則不需計算眷保 health_rate = 0.0517
            if is_comp:
                amount = wage * health_rate * health_dependents_average * health_insurer_company_pay * day
                # amount = com_health_rate_pay * day
            else:
                amount = self.old_round(math.floor(wage * health_rate * health_insurer_pay * day * 10000) / 10000.0)
                # amount = self.old_round(math.floor(insurance_history_data.health_insurance_gap_id.employee_pay * day * 10000) / 10000.0)
                # # 計算眷保
                # if dependents_data:
                #     for dependent in dependents_data:
                #         if dependent.cancel_insurance_time and dependent.cancel_insurance_time < last_day:
                #             total_amount += 0
                #         else:
                #             total_amount += self.old_round(amount * float(dependent.health_rate))
                dependents_cost = self.caculate_healthy_dependents(dependents_data, amount)
                total_amount += dependents_cost
            total_amount += amount * subsidy
            total_amount = math.floor(total_amount * 10000) / 10000.0
            total_amount = self.old_round(total_amount)
        return total_amount

    def caculate_healthy_dependents(self, dependents, amount):
        cost = 0
        for dependent in dependents:
            cost += self.old_round(amount * float(dependent.health_rate))       
        return cost

    def healthy_dependents(self, employee_id, date_from, date_to, rule_code='Healthy', is_comp=False):
        amount_end = False
        total_amount = 0
        employee = self.env['hr.employee'].browse(employee_id)
        rule = self.env['hr.salary.rule'].search([('code', '=', rule_code)])
        # 健異動歷程
        pay_data = self.env['hr.health.insurance.history'].search([('health_insurance_history_id', '=', employee_id)],
                                                                  order='start_date')
        on_day_pay = pay_data.filtered(lambda r: date_to >= r.start_date >= date_from)
        active_check = pay_data.filtered(lambda r: date_to >= r.start_date)
        setting = self.env['ir.config_parameter'].sudo()
        health_rate = float(setting.get_param('health_rate', default=False)) / 100  # 健保費率
        health_insurer_pay = float(setting.get_param('health_insurer_pay', default=False)) / 100  # 健保保險人負擔比率
        health_insurer_company_pay = float(setting.get_param('health_insurer_company_pay', default=False)) / 100  # 健保投保單位負擔比率
        health_dependents_max = int(setting.get_param('health_dependents_max', default=False))  # 眷口數上限
        health_dependents_average = float(setting.get_param('health_dependents_average', default=False)) + 1  # 平均眷口數
        dependents_data = self.env['hr.dependents.information'].search([('employee_id', '=', employee_id), ('add_insurance_time', '<=', date_to)],
                                                                       limit=health_dependents_max)  # 健保眷屬明細
        first_day_of_month = date_from.replace(day=1)
        last_day_of_month = (first_day_of_month.replace(month=first_day_of_month.month % 12 + 1,
                                                        year=first_day_of_month.year + first_day_of_month.month // 12) - timedelta(days=1))

        last_day = last_day_of_month
        # 判斷離職時間點
        day = self.env['hr.payslip'].baseline(on_day_pay, rule, employee, date_from, date_to, True)
        is_legal_agent = False
        # 判斷是否為最後一筆
        # 確認當月有無變更級距，有則使用異動資料
        if on_day_pay:
            is_last_day = last_day_of_month - date_to
            insurance_history_data = on_day_pay[len(on_day_pay) - 1]
            wage = float(insurance_history_data.health_insurance_gap_id.insurance_salary)
            emp_health_rate_pay = float(insurance_history_data.health_insurance_gap_id.employee_pay)
            com_health_rate_pay = float(insurance_history_data.health_insurance_gap_id.company_pay)
            legal_health_rate_pay = float(insurance_history_data.health_insurance_gap_id.legal_pay)
            subsidy = float(insurance_history_data.health_rate)
            # 如最後一筆資料為退保，並且非最後一天退保，則當月不保
            if insurance_history_data.change_reason_selection == 'off':
                wage = float(pay_data[pay_data.ids.index(insurance_history_data.id) - 1].health_insurance_gap_id.insurance_salary)
                emp_health_rate_pay = 0
                com_health_rate_pay = 0
                legal_health_rate_pay = 0
            if insurance_history_data.change_reason_selection == 'off' and insurance_history_data.start_date < last_day or is_last_day:
                wage = 0
                emp_health_rate_pay = 0
                com_health_rate_pay = 0
                legal_health_rate_pay = 0
            if insurance_history_data.heath_rate_type == 'legal':
                is_legal_agent = True
        # 無變更直接使用明細資料
        else:
            is_last_day = last_day_of_month - date_to
            if active_check and not is_last_day:
                valid_data = pay_data.filtered(lambda r: date_from >= r.start_date).sorted(key='start_date', reverse=True)[:1]
                wage = float(valid_data.health_insurance_gap)
                emp_health_rate_pay = float(valid_data.health_insurance_gap_id.employee_pay)
                com_health_rate_pay = float(valid_data.health_insurance_gap_id.company_pay)
                legal_health_rate_pay = float(valid_data.health_insurance_gap_id.legal_pay)
                subsidy = float(valid_data.health_rate)
                if valid_data.heath_rate_type == 'legal':
                    is_legal_agent = True
            else:
                wage = 0
                subsidy = 0
                emp_health_rate_pay = 0
                com_health_rate_pay = 0
                legal_health_rate_pay = 0

        # 雇主身份 以雇主費率計算
        if is_legal_agent:
            # 計算出個人要負擔金額
            amount = self.old_round(math.floor(legal_health_rate_pay * day * 10000) / 10000.0)
            # 計算眷保
            if dependents_data:
                for dependent in dependents_data:
                    if dependent.cancel_insurance_time and dependent.cancel_insurance_time < last_day:
                        total_amount += 0
                    else:
                        total_amount += self.old_round(amount * float(dependent.health_rate))
            # total_amount += amount
        else:
            # 計算出個人要負擔金額
            amount = self.old_round(math.floor(wage * health_rate * health_insurer_pay * day * 10000) / 10000.0)
            # 計算眷保
            if dependents_data:
                for dependent in dependents_data:
                    if dependent.cancel_insurance_time and dependent.cancel_insurance_time < last_day:
                        total_amount += 0
                    else:
                        total_amount += self.old_round(amount * float(dependent.health_rate))
            # total_amount += amount * subsidy
            total_amount = math.floor(total_amount * 10000) / 10000.0
            total_amount = self.old_round(total_amount)
        return total_amount

    # 勞退
    def labor_pension(self, employee_id, date_from, date_to, rule_code='COMP_Labor_Pension', count_type=0):
        employee = self.env['hr.employee'].browse(employee_id)
        rule = self.env['hr.salary.rule'].search([
            ('code', '=', rule_code),
            ('company_id', '=', employee.company_id.id)
        ], limit=1)
        # 異動歷程
        change_history = self.env['hr.labor.pension.history'].search([('employee_id', '=', employee_id)], order='start_date')
        active_check = change_history.filtered(lambda r: date_to >= r.start_date)  # 確認當月有效的歷程紀錄
        on_day_history = change_history.filtered(lambda r: date_to >= r.start_date >= date_from)  # 落於薪資起迄區間的歷程紀錄
        setting = self.env['ir.config_parameter'].sudo()
        labor_pension_rate = float(setting.get_param('default_labor_pension_comp_rate', default='0.06'))  # 勞退費率
        first_day_of_month = date_from.replace(day=1)
        last_day_of_month = (first_day_of_month.replace(month=first_day_of_month.month % 12 + 1,
                                                        year=first_day_of_month.year + first_day_of_month.month // 12) - timedelta(days=1))
        first_day = first_day_of_month - date_from
        last_day = last_day_of_month - date_to
        # 無變更紀錄代表薪資為原樣，無須多段計算
        if not on_day_history and not first_day and not last_day:
            if active_check:
                valid_data = change_history.filtered(lambda r: date_from >= r.start_date).sorted(key='start_date', reverse=True)[:1]
                if count_type == 20:  # 公司提撥
                    day_pay = self.old_round(valid_data.labor_pension_salary * float(labor_pension_rate))
                elif count_type == 21:  # 自提
                    day_pay = self.old_round(valid_data.labor_pension_salary * float(valid_data.self_reimbursement_of_labor_pension))
            else:
                day_pay = 0
        else:
            employee.is_payslip_compute = True
            set_zero = self.env['hr.labor.pension.gap'].sudo().search([('insurance_level', '=', 0)], order="create_date desc", limit=1)
            # set_zero.is_retire = True
            set_zero_id = set_zero.id
            change_data = []
            first_day_data = self.env['hr.labor.pension.history']
            # 開始日非當月第一天
            if first_day:
                front = self.env['hr.labor.pension.history'].search([('employee_id', '=', employee_id), ('start_date', '<=', date_from)],
                                                                    order='start_date desc', limit=1)
                if front.start_date != date_from:
                    change_data.append({'start_date': front.start_date, 'id': front.id})
                    front.start_date = date_from
            # 結束日非當月最後一天
            if last_day:
                after = self.env['hr.labor.pension.history'].search([('employee_id', '=', employee_id), ('start_date', '>=', date_to)], order='start_date asc',
                                                                    limit=1)
                last_front = self.env['hr.labor.pension.history'].search([('employee_id', '=', employee_id), ('start_date', '<', date_to)],
                                                                         order='start_date desc', limit=1)
                # 當天結束點沒有異動資料，加入0代表停止點
                if after.start_date != date_to:
                    first_day_data += self.env['hr.labor.pension.history'].sudo().create(
                        {'employee_id': employee_id, 'start_date': date_to,
                         'self_reimbursement_of_labor_pension': '0.00', 'labor_pension_gap_id': set_zero_id,
                         'labor_pension_salary': 0.0,
                         'change_reason_selection': 'add' if last_front.change_reason_selection not in ['add', 'promote', 'self_contribution'] else 'off'})
                # 有資料但是是加保，將該筆資料移動到他日再進行停止點的加入
                elif after.change_reason_selection in ['add', 'promote']:
                    change_data.append({'start_date': after.start_date, 'id': after.id})
                    after.start_date = after.start_date + timedelta(days=2)
                    first_day_data += self.env['hr.labor.pension.history'].sudo().create(
                        {'employee_id': employee_id, 'start_date': date_to,
                         'self_reimbursement_of_labor_pension': '0.00', 'labor_pension_gap_id': set_zero_id,
                         'labor_pension_salary': 0.0,
                         'change_reason_selection': 'add' if last_front.change_reason_selection not in ['add', 'promote', 'self_contribution'] else 'off', })
            # 如果沒有增加前方的資料就要在這裡補上
            if not first_day:
                front = self.env['hr.labor.pension.history'].search([('employee_id', '=', employee_id), ('start_date', '<=', date_from)],
                                                                    order='start_date desc', limit=1)
                first_day_data += self.env['hr.labor.pension.history'].sudo().create(
                    {'employee_id': front.employee_id.id, 'start_date': date_from,
                     'self_reimbursement_of_labor_pension': front.self_reimbursement_of_labor_pension,
                     'labor_pension_gap_id': front.labor_pension_gap_id.id,
                     'labor_pension_salary': front.labor_pension_salary,
                     'change_reason_selection': 'add' if front.change_reason_selection not in ['add', 'promote', 'self_contribution'] else 'off', })
            # 因為開始日非當月第一天或結束日非當月最後一天，因此強制只接收區間內的資料
            if first_day or last_day:
                change_history = self.env['hr.labor.pension.history'].search([('employee_id', '=', employee_id)], order='start_date')
                on_day_history = change_history.filtered(lambda r: date_to >= r.start_date >= date_from)
                change_history = on_day_history
            day_pay = self.env['hr.payslip'].count_day_wage(change_history, on_day_history, date_from, date_to, count_type)
            # set_zero.is_retire = False
            # employee_id.is_payslip_compute = False
            if first_day_data:
                first_day_data.unlink()
            for original in change_data:
                self.env['hr.labor.pension.history'].search([('id', '=', original['id'])]).start_date = original[
                    'start_date']
        # 單日薪水另外處理
        if date_from == date_to:
            front = self.env['hr.labor.pension.history'].search([('employee_id', '=', employee_id), ('start_date', '<=', date_from)], order='start_date desc',
                                                                limit=1)
            # 勞退自提要多設一個自提比例
            if count_type == 21:
                day_pay = [{'wage': front.labor_pension_salary, 'part_day': 1,
                            'self_labor_pension': float(front.self_reimbursement_of_labor_pension)}]
            else:
                day_pay = [{'wage': front.labor_pension_salary, 'part_day': 1}]

        day = self.env['hr.payslip'].baseline(day_pay, rule, employee, date_from, date_to, True)
        # count_type = 21 代表是勞退自提，不適用公司提繳費率
        if count_type == 21:
            labor_pension_rate = 0.0
        amount = self.old_round(self.env['hr.payslip'].labor_pension_days(day_pay, employee, date_from, date_to, labor_pension_rate, day))
        return amount

    # 統計績效獎金
    def performance_bonus(self, employee_id, date_from, date_to, rule_code='performance_bonus'):
        total_amount = sum(self.env['sl.bonus.record'].search(
            [('employee_id', '=', employee_id), ('payroll_allocation_day', '>=', date_from),
             ('payroll_allocation_day', '<=', date_to), ('salary_rule_id.code', '=', rule_code)]).mapped('amount'))
        return total_amount

    def other_bonus(self, employee_id, date_from, date_to, rule_code='other_bonus'):
        total_amount = sum(self.env['sl.bonus.record'].search(
            [('employee_id', '=', employee_id), ('payroll_allocation_day', '>=', date_from),
             ('payroll_allocation_day', '<=', date_to), ('salary_rule_id.code', '=', rule_code)]).mapped('amount'))
        return total_amount

    def festival_bonus(self, employee_id, date_from, date_to, rule_code='festival_bonus'):
        total_amount = sum(self.env['sl.bonus.record'].search(
            [('employee_id', '=', employee_id), ('payroll_allocation_day', '>=', date_from),
             ('payroll_allocation_day', '<=', date_to), ('salary_rule_id.code', '=', rule_code)]).mapped('amount'))
        return total_amount

    def dividend_bonus(self, employee_id, date_from, date_to, rule_code='dividend_bonus'):
        total_amount = sum(self.env['sl.bonus.record'].search(
            [('employee_id', '=', employee_id), ('payroll_allocation_day', '>=', date_from),
             ('payroll_allocation_day', '<=', date_to), ('salary_rule_id.code', '=', rule_code)]).mapped('amount'))
        return total_amount

    def attendance_bonus(self, employee_id, date_from, date_to, rule_code='attendance_bonus'):
        total_amount = sum(self.env['sl.bonus.record'].search(
            [('employee_id', '=', employee_id), ('payroll_allocation_day', '>=', date_from),
             ('payroll_allocation_day', '<=', date_to), ('salary_rule_id.code', '=', rule_code)]).mapped('amount'))
        return total_amount

    def birthday_bonus(self, employee_id, date_from, date_to, rule_code='birthday_bonus'):
        total_amount = sum(self.env['sl.bonus.record'].search(
            [('employee_id', '=', employee_id), ('payroll_allocation_day', '>=', date_from),
             ('payroll_allocation_day', '<=', date_to), ('salary_rule_id.code', '=', rule_code)]).mapped('amount'))
        return total_amount

    def overtime_withoutrest_allowance(self, employee_id, date_from, date_to, rule_code='overtime_withoutrest_allowance'):
        ir_parameter = self.env['ir.config_parameter'].sudo()
        month_hour = float(ir_parameter.get_param('overtime_withoutrest_amount', default=False))  # 誤餐費費用 per 0.5小時
        self.env['starrylord.overtime.apply'].search(('employee_id', '=', employee_id), ('start_day', '>=', date_from),
             ('start_day', '<=', date_to), ('has_overtime_meal_allowance', '=', True))

    def overtime_meal_allowance(self, employee_id, date_from, date_to, rule_code='attendance_bonus'):
        # 誤餐費計算
        # 取得有誤餐費的加班單
        ir_parameter = self.env['ir.config_parameter'].sudo()
        overtime_meal_fee = float(ir_parameter.get_param('overtime.meal.fee', default=150))  # 誤餐費費用 per 0.5小時
        has_meal_allowance_overtime_apply_ids = self.env['starrylord.overtime.apply'].search([('employee_id', '=', employee_id), ('state', '=', 'agree'),
                                                                                              ('has_overtime_meal_allowance', '=', True),
                                                                                              ('start_day', '>=', date_from), ('start_day', '<=', date_to)])

        total_amount = len(has_meal_allowance_overtime_apply_ids) * overtime_meal_fee
        return total_amount

    # 計算薪資實付金額
    def compute_taxable_add_subtotal(self):
        for res in self:
            # 非經常性薪資超過扣除標準額, 需代扣5%所得稅
            sum_non_recurring_income = 0
            over_tax_payslip_line = res.payslip_line_ids.filtered(lambda r: r.code == 'personal_tax')
            if over_tax_payslip_line:
                sum_non_recurring_income = sum(res.payslip_line_ids.filtered(lambda r: r.salary_rule_id.is_non_recurring is True).mapped('amount'))
                over_tax_payslip_line.amount = self.old_round(sum_non_recurring_income * 0.05) if sum_non_recurring_income >= res.over_tax_amount else 0.0

            # 計算二代健保補充保費
            supplementary_payslip_line = res.payslip_line_ids.filtered(lambda r: r.code == 'Supplementary')
            # 如果薪資認列月份是12月,必須計算前一年度經常性薪資總額,扣除二代健保補充保費
            if supplementary_payslip_line and res.salary_date.strftime('%m') == '12':
                # 統計前一年度1/1 ~ 12/31 非經常性薪資總額
                sum_non_recurring_income = 0
                start_day = res.salary_date - relativedelta(years=1) + relativedelta(day=1, month=1)
                end_day = res.salary_date - relativedelta(days=1) + relativedelta(day=31, month=12)
                sum_non_recurring_income = sum(self.env['hr.payslip.line'].search(
                    [('payslip_id.employee_id', '=', res.employee_id.id), ('date_from', '>=', start_day), ('date_from', '<=', end_day),
                     ('salary_rule_id.is_non_recurring', '=', 'True')]).mapped('amount'))
                if sum_non_recurring_income >= res.health_insurance_salary * 4:
                    supplementary_amount = self.old_round((sum_non_recurring_income - res.health_insurance_salary * 4) * 0.0211)
                    supplementary_payslip_line.amount = supplementary_amount

            # # 重新計算請假扣款
            # holiday_payslip_line = res.payslip_line_ids.filtered(lambda r: r.code == 'holiday')
            # if holiday_payslip_line:
            #     holiday_amount = self.env['hr.payslip'].holiday(res.employee_id.id, res.holiday_ids,
            #                                                     res.employee_payslip_salary_setting_ids)
            #     holiday_payslip_line.amount = holiday_amount
            #
            # # 重新計算加班費
            # overtime_payslip_line = res.payslip_line_ids.filtered(lambda r: r.code == 'overtime')
            # if overtime_payslip_line:
            #     overtime_amount = self.env['hr.payslip'].overtime(res.employee_id.id, res.overtime_ids, res.overtime_holiday_ids,
            #                                                       res.employee_payslip_salary_setting_ids)
            #     overtime_payslip_line.amount = overtime_amount

            taxable_add_subtotal, taxfree_add_subtotal, company_cost = 0.0, 0.0, 0.0
            for wage in res.payslip_line_ids.filtered(lambda x: x.category_id.code == 'Taxable_Add'):
                taxable_add_subtotal += wage.amount
            for wage in res.payslip_line_ids.filtered(lambda x: x.category_id.code == 'Taxfree_Add'):
                taxfree_add_subtotal += wage.amount
            for wage in res.payslip_line_ids.filtered(lambda x: x.category_id.code == 'COMP'):
                company_cost += wage.amount
            basic_wage = 0
            for wage in res.payslip_line_ids.filtered(lambda x: x.salary_rule_id.code == 'BASIC_Wage'):
                basic_wage += wage.amount

            for wage in res.payslip_line_other_ids.filtered(lambda x: x.category_id.code == 'Taxable_Add'):
                taxable_add_subtotal += wage.amount
            for wage in res.payslip_line_other_ids.filtered(lambda x: x.category_id.code == 'Taxfree_Add'):
                taxfree_add_subtotal += wage.amount
            for wage in res.payslip_line_other_ids.filtered(lambda x: x.category_id.code == 'COMP'):
                company_cost += wage.amount
            for wage in res.payslip_line_other_ids.filtered(lambda x: x.salary_rule_id.code == 'BASIC_Wage'):
                basic_wage += wage.amount

            res.basic_wage = basic_wage

            res.payable_add_subtotal = taxable_add_subtotal + taxfree_add_subtotal
            res.taxable_add_subtotal = taxable_add_subtotal
            res.taxfree_add_subtotal = taxfree_add_subtotal
            res.company_cost = company_cost
            
        self.recompute_auto_rules()
        
        # 受自動計算項目的影響，減項放最後算
        for res in self:
            taxable_decrease_subtotal, taxfree_decrease_subtotal = 0.0, 0.0
            for wage in res.payslip_line_ids.filtered(lambda x: x.category_id.code == 'Taxable_Decrease'):
                taxable_decrease_subtotal += wage.amount
            for wage in res.payslip_line_other_ids.filtered(lambda x: x.category_id.code == 'Taxable_Decrease'):
                taxable_decrease_subtotal += wage.amount
            for wage in res.payslip_line_ids.filtered(lambda x: x.category_id.code == 'Taxfree_Decrease'):
                taxfree_decrease_subtotal += wage.amount
            for wage in res.payslip_line_other_ids.filtered(lambda x: x.category_id.code == 'Taxfree_Decrease'):
                taxfree_decrease_subtotal += wage.amount
            res.taxable_decrease_subtotal = taxable_decrease_subtotal
            res.taxfree_decrease_subtotal = taxfree_decrease_subtotal
            res.deduction_subtotal = taxable_decrease_subtotal + taxfree_decrease_subtotal
            res.all_subtotal = res.taxable_add_subtotal - res.taxable_decrease_subtotal + res.taxfree_add_subtotal - res.taxfree_decrease_subtotal
        
    def baseline(self, amount, rule, employee, date_from, date_to, is_compute=False):
        # 將下個月時間拉出
        date_from_next_month = date_from + relativedelta(months=1)
        # 依實際天數且不超過30天
        if rule.baseline == 'days':
            # 將下個月第一天拉出，並減一天就是本月最後一天
            lastday = datetime(date_from_next_month.year, date_from_next_month.month, 1) - timedelta(days=1)
            if lastday.day > 30:
                lastday -= timedelta(days=1)
            if is_compute:
                amount = lastday.day
            else:
                amount = amount
        # 依實際天數
        if rule.baseline == 'month_days':
            # 將下個月第一天拉出，並減一天就是本月最後一天
            lastday = datetime(date_from_next_month.year, date_from_next_month.month, 1) - timedelta(days=1)
            if is_compute:
                amount = lastday.day
            else:
                amount = amount
        # 直接計薪
        if rule.baseline == 'no_days':
            amount = amount
        # 不計薪
        if rule.baseline == 'no':
            # amount = amount
            # if employee.registration_date:
            #     if employee.registration_date <= date_from:
            #         amount = 0
            # if employee.resignation_date:
            #     if employee.resignation_date <= date_to:
            amount = 0
        # 健保
        if rule.baseline == 'healthy':
            # 在職或當月最後一天離職需繳交健保
            if is_compute:
                # if employee.resignation_date:
                #     last_check = date_to + relativedelta(months=+1, day=1, days=-1)
                #     if employee.resignation_date != last_check:
                #         amount = 0
                # else:
                amount = 1
            else:
                amount = amount
        # 勞保
        if rule.baseline == 'labor':
            if is_compute:
                amount = 30
            else:
                amount = amount
        return amount

    @api.onchange('employee_id')
    def onchange_employee_id(self):
        if self.employee_id:
            self.payroll_structure_id = self.employee_id.payroll_structure_id

    @api.onchange('salary_date')
    def onchange_salary_date(self):
        if self.salary_date:
            # 自動帶入薪資計算起迄第一天跟最後一天
            self.date_from = self.salary_date.replace(day=1)
            self.date_to = self.salary_date.replace(day=1) + relativedelta(months=1, days=-1)

    def action_payslip_draft(self):
        self.state = "draft"

    #     return self.write({"state": "draft"})

    def action_payslip_done(self):
        self.state = "confirm"

    def action_payslip_cancel(self):
        return self

    def print_payslip(self):
        return self.env.ref('sl_hrm_payroll.action_report_hr_payslip').report_action(self)

    def action_payslip_form(self):
        return {
            'name': _('檢視薪資單'),
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'hr.payslip',
            'view_id': self.env.ref('sl_hrm_payroll.hr_payslip_form_view').id,
            'type': 'ir.actions.act_window',
            'res_id': self.id,
            'target': 'current',
            'context': {'create': 0}
        }

    def action_payslip_bonus_form(self):
        return {
            'name': _('檢視獎金單'),
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'hr.payslip',
            'view_id': self.env.ref('sl_hrm_payroll.hr_payslip_bonus_form_view').id,
            'type': 'ir.actions.act_window',
            'res_id': self.id,
            'target': 'current',
            'context': {'create': 0}
        }

    def action_generate_pdf(self):
        for payslip in self:
            template_id = self.env.ref('sl_hrm_payroll.action_report_hr_payslip')
            pdf = template_id._render_qweb_pdf(template_id.id, [payslip.id])[0]
            output_buffer = io.BytesIO()
            pdf_writer = PdfWriter()
            pdf_reader = PdfReader(io.BytesIO(pdf))
            for page in pdf_reader.pages:
                pdf_writer.add_page(page)
            password = payslip.employee_id.identification_id if payslip.employee_id.identification_id else '123456'
            # pdf_writer.encrypt(user_pwd=password, owner_pwd=password, use_128bit=True)
            # Save the encrypted PDF to buffer
            pdf_writer.write(output_buffer)
            data_record = base64.b64encode(output_buffer.getvalue())

            payroll_report_attachment = self.env['ir.attachment'].create({
                'name': _('%s薪資單-%s') % (payslip.salary_date.strftime('%Y-%m'), payslip.employee_id.name),
                'datas': data_record,
                'res_model': 'hr.payslip',
                'res_id': payslip.id,
                'type': 'binary',
                'mimetype': 'application/pdf',
                'public': True
            })

            payslip.write({'payroll_report_attachment_ids': [(6, 0, [payroll_report_attachment.id])]})

    def send_mail_report(self):
        for payslip in self:
            email_template = self.env.ref(
                'sl_hrm_payroll.email_template_payroll_report')
            email = payslip.employee_id.work_email
            if email_template and email:
                email_values = {
                    'email_to': email,
                    'email_cc': False,
                    'scheduled_date': False,
                    'recipient_ids': [],
                    'partner_ids': [],
                    'auto_delete': True,
                }
                email_template.attachment_ids = [
                    (4, payslip.payroll_report_attachment_ids[0].id)]
                email_template.with_context({'name': payslip.name}).send_mail(
                    self.id, email_values=email_values, force_send=True)
                email_template.attachment_ids = [(5, 0, 0)]
                payslip.is_payslip_sent = True
                payslip.payslip_sent_date = datetime.now()

    def open_salary_rule_add_wizard(self):
        return {
            'type': 'ir.actions.act_window',
            'name': '新增薪資規則',
            'res_model': 'wizard.payslip.salary.rule.add',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_salary_rule_id': False,  # 可設定默認值
                'default_amount': 0.0,
                'active_id': self.id,  # 傳遞當前薪資單 ID
                'company_id': self.env.company.id,
            },
        }
      