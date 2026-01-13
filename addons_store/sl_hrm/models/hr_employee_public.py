from odoo import models, fields, api
from odoo.exceptions import ValidationError, UserError


class HrEmployeePublicInheritance(models.Model):
    _inherit = "hr.employee.public"
    _order = "employee_number asc"

    employee_number = fields.Char(string='員工編號')
    substitute_id = fields.Many2one('hr.employee.public', string='代理人')
    # MVPN
    mvpn = fields.Char(string='MVPN', readonly=True)
    # 公司分機
    office_phone = fields.Char(string='公司分機', readonly=True)

    state = fields.Selection(
            related='employee_id.state',
            string='狀態',
            readonly=True,
            store=True
        )
