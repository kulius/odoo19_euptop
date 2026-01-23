from odoo import api, models, fields, _


class User(models.Model):
    _inherit = 'res.users'

    employee_number = fields.Char(related='employee_id.employee_number', string='員工編號')
    substitute_id = fields.Many2one(related='employee_id.substitute_id', string='代理人', groups="hr.group_hr_user")

    @api.model_create_multi
    def create(self, vals_list):
        # set default password ID Number + '1234'
        for vals in vals_list:
            if vals.get('password', _('_New')) == _('_New'):
                # 密碼規則 email 取字串到 '@' + '@' + 公司編號
                login_prefix = vals['login'].split('@')[0]
                # password = login_prefix + '@' + self.env.user.company_id.vat
                password = login_prefix
                vals['password'] = password
        res = super().create(vals_list)
        return res
