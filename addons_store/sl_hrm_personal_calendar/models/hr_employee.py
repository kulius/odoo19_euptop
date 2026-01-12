from odoo import models, fields, api
from odoo.exceptions import ValidationError, UserError


class HrEmployeeInheritance(models.Model):
    _inherit = "hr.employee"

    schedule_id = fields.Many2one('hr.schedule', string='適用班別')
