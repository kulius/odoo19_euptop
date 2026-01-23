from odoo import api, fields, models


class HrPayrollStructure(models.Model):
    _name = 'hr.payroll.structure'
    _description = '薪資結構'

    name = fields.Char(required=True)
    code = fields.Char(string='Reference', required=True)
    company_id = fields.Many2one('res.company', string='Company', required=True, default=lambda self: self.env.company)
    note = fields.Text(string='Description')
    parent_id = fields.Many2one('hr.payroll.structure', string='Parent')
    children_ids = fields.One2many('hr.payroll.structure', 'parent_id', string='Children', copy=True)
    rule_ids = fields.Many2many('hr.salary.rule', 'hr_structure_salary_rule_rel', 'struct_id', 'rule_id',
                                string='Salary Rules')
    auto_recompute_rule_ids = fields.Many2many(
        'hr.salary.rule',
        'structure_auto_recompute_rule_rel',
        'structure_id', 'rule_id',
        string='自動重新計算的薪資項目',
        help='當有依賴項目金額變動時，這些項目會自動重新計算'
    )

    def _recursive_search_of_rules(self):
        """
        @return: returns a list of tuple (id, sequence) which are all the
                 children of the passed rule_ids
        """
        children_rules = []
        for rule in self.filtered(lambda rule: rule.child_ids):
            children_rules += rule.child_ids._recursive_search_of_rules()
        return [(rule.id, rule.sequence) for rule in self] + children_rules

    def get_all_rules(self):
        """
        @return: returns a list of tuple (id, sequence) of rules that are maybe
                 to apply
        """
        all_rules = []
        for struct in self:
            all_rules += struct.rule_ids._recursive_search_of_rules()

        return all_rules
        #
        #
        # return [(all_rules.id, all_rules.sequence) for all_rules in self]
