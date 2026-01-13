from odoo import models


class HrDepartmentInherit(models.Model):
    _inherit = 'hr.department'

    def batch_update_department(self):
        new_manager_id = self.manager_id
        if new_manager_id:
            # 批次更新部門員工的主管
            self.env['hr.employee'].search([('department_id', '=', self.id)]).write({'parent_id': new_manager_id})
