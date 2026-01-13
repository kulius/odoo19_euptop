from odoo import api, fields, models, _
from odoo.exceptions import UserError
import datetime
import logging
from dateutil.relativedelta import relativedelta

_logger = logging.getLogger(__name__)


class StarryLordHrAutoJob(models.TransientModel):
    _name = 'sl.hr.auto.job'
    _description = '人資自動化動作'

    def job_run(self):
        # find out today resign employee
        employee_ids = self.env['hr.employee'].search([('active', '=', True), ('state', '=', 'resign')])

        for employee_id in employee_ids:
            employee_id.user_id.active = False
            employee_id.active = False

    def job_auto_create_on_board_user(self):
        #  找出當日到職員工
        _logger.info('job_auto_create_on_board_user %s ' % datetime.date.today())
        default_employee_template = self.env['hr.employee'].search([('user_id.login', '=', 'admin')], limit=1)
        domain = [('active', '=', True), ('user_id', '=', False), ('work_email', '!=', False), ]
        all_employee_ids = self.env['hr.employee'].search(domain)
        #  如果尚未開通res.user, 則自動建立
        for employee in all_employee_ids:
            employee.compute_state()  # 更新員工狀態
            if not employee.user_id and employee.state == 'working' and employee.registration_date == datetime.date.today():

                # auto create res.users
                res_user = self.env['res.users'].create({
                    'name': employee.name,
                    'login': employee.work_email,
                    'email': employee.work_email,
                })

                # link res.users to hr.employee
                employee.user_id = res_user.id
                employee.payroll_structure_id = default_employee_template.payroll_structure_id.id
                employee.schedule_id = default_employee_template.schedule_id.id
