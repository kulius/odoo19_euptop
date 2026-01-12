from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
from odoo.tools.safe_eval import safe_eval

class HrSalaryRule(models.Model):
    _name = 'hr.salary.rule'
    _order = 'sequence, id'
    _description = '薪資規則'

    name = fields.Char(required=True, translate=True)
    code = fields.Char(required=True, help="")
    sequence = fields.Integer(required=True, index=True, default=5,
                              help='Use to arrange calculation sequence')
    quantity = fields.Char(default='1.0',
                           help="")
    category_id = fields.Many2one('hr.salary.rule.category', string='薪資分類', required=True)
    active = fields.Boolean(default=True,
                            help="")
    appears_on_payslip = fields.Boolean(string='是否顯示在薪資單上', default=True,
                                        help="Used to display the salary rule on payslip.")
    baseline = fields.Selection([('days', '依實際天數且上限30天'),
                                 ('month_days', '依實際天數'),
                                 ('no_days', '直接計薪'),
                                 ('no', '不計薪'),
                                 ('healthy', '健保'),
                                 ('labor', '勞保')],
                                string="破月計薪方式")
    parent_rule_id = fields.Many2one('hr.salary.rule', string='Parent Salary Rule', index=True)
    company_id = fields.Many2one('res.company', string='Company',
                                 default=lambda self: self.env.company)
    condition_select = fields.Selection(
        [("none", "總為真"), ("range", "範圍"), ("python", "Python表達式")],
        string="條件根據",
        default="none",
        required=True,
    )

    condition_range = fields.Char(string='Range Based on', default='contract.wage',
                                  help='')
    condition_python = fields.Text(string='Python Condition', required=True,
                                   default="""
            # Available variables:
            #----------------------
            # payslip: object containing the payslips
            # payslip.rule_parameter(code): get the value for the rule parameter specified.
            #   By default it gets the code for payslip date.
            # employee: hr.employee object
            # contract: hr.contract object
            # rules: object containing the rules code (previously computed)
            # categories: object containing the computed salary rule categories
            #    (sum of amount of all rules belonging to that category).
            # worked_days: object containing the computed worked days
            # inputs: object containing the computed inputs
            # payroll: object containing miscellaneous values related to payroll
            # current_contract: object with values calculated from the current contract

            # Available compute variables:
            #-------------------------------
            # result: returned value have to be set in the variable 'result'

            # Example:
            #-------------------------------
            result = rules.NET > categories.NET * 0.10

            """,
                                   help='')
    condition_range_min = fields.Float(string='Minimum Range', help="The minimum amount, applied for this rule.")
    condition_range_max = fields.Float(string='Maximum Range', help="The maximum amount, applied for this rule.")
    amount_select = fields.Selection([
        ('percentage', 'Percentage (%)'),
        ('fix', 'Fixed Amount'),
        ('code', 'Python Code'),
    ], string='Amount Type', index=True, required=True, default='fix',
        help="The computation method for the rule amount.")
    
    computed_amount_label = fields.Char(
        string="計算方式",
        compute="_compute_amount_label",
        store=True  
    )
    amount_fix = fields.Float(string='Fixed Amount', digits='Payroll')
    amount_percentage = fields.Float(string='Percentage (%)', digits='Payroll Rate',
                                     help='For example, enter 50.0 to apply a percentage of 50%')
    amount_python_compute = fields.Text(string='Python Code',
                                        default='')
    amount_percentage_base = fields.Char(string='Percentage based on', help='result will be affected to a variable')
    child_ids = fields.One2many('hr.salary.rule', 'parent_rule_id', string='Child Salary Rule', copy=True)

    note = fields.Text(string='Description')
    struct_id = fields.Many2one('hr.payroll.structure', string='Salary Structure')
    is_basic = fields.Boolean(string='是否為本薪')
    is_inherit_setting = fields.Boolean(string='禁用每月沿用按鈕')
    is_non_recurring = fields.Boolean(string='非經常性薪資', default=False)
    is_withholding = fields.Boolean(string='稅費項目', default=False)

    _sql_constraints = [
        (
            'unique_code_company',
            'unique(code, company_id)',
            '每個公司內的薪資規則代碼必須唯一。'
        ),
    ]

    @api.depends('amount_select')
    def _compute_amount_label(self):
        for record in self:
            if record.amount_select == 'code':
                record.computed_amount_label = "系統計算"
            elif record.amount_select == 'percentage':
                record.computed_amount_label = "百分比"
            else:
                record.computed_amount_label = "固定金額"
    def _recursive_search_of_rules(self):
        """
        @return: returns a list of tuple (id, sequence) which are all the
                 children of the passed rule_ids
        """
        children_rules = []
        for rule in self.filtered(lambda rule: rule.child_ids):
            children_rules += rule.child_ids._recursive_search_of_rules()
        return [(rule.id, rule.sequence) for rule in self] + children_rules

    def _compute_rule(self, localdict):
        self.ensure_one()
        if self.amount_select == "fix":
            try:
                # if self.env['alltop.payslip.employee.setting'].search([('employee_id', '=', localdict['employee'].id)]):
                #
                return (
                    self.amount_fix,
                    float(safe_eval(self.quantity, localdict)),
                    100.0,
                    False,  # result_name is always False if not computed by python.
                )
            except Exception:
                raise UserError(
                    _("Wrong quantity defined for salary rule %s (%s).")
                    % (self.name, self.code)
                )
        elif self.amount_select == "percentage":
            try:
                return (
                    float(safe_eval(self.amount_percentage_base, localdict)),
                    float(safe_eval(self.quantity, localdict)),
                    self.amount_percentage,
                    False,  # result_name is always False if not computed by python.
                )
            except Exception:
                raise UserError(
                    _(
                        "Wrong percentage base or quantity defined for salary "
                        "rule %s (%s)."
                    )
                    % (self.name, self.code)
                )
        else:
            try:
                # safe_eval中第一欄為要執行的python code，第二欄為要傳入的變數，第三欄為執行模式，第四欄為是否複製
                safe_eval(
                    self.amount_python_compute, localdict, mode="exec", nocopy=True
                )
                result_qty = 1.0
                result_rate = 100.0
                result_name = True
                if "result_name" in localdict:
                    result_name = localdict["result_name"]
                if "result_qty" in localdict:
                    result_qty = localdict["result_qty"]
                if "result_rate" in localdict:
                    result_rate = localdict["result_rate"]
                return (
                    float(localdict["result"]),
                    float(result_qty),
                    float(result_rate),
                    result_name,
                )
            except Exception as ex:
                raise UserError(
                    _(
                        """
薪資規則的 Python 代碼定義錯誤 %s (%s).
以下為錯誤資訊:

%s
"""
                    )
                    % (self.name, self.code, repr(ex))
                )
