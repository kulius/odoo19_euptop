from odoo import api, fields, models, _
from odoo.exceptions import UserError
import datetime, logging
from dateutil.relativedelta import relativedelta

_logger = logging.getLogger(__name__)


class StarryLordHrAttendanceJob(models.TransientModel):
    _name = 'sl.hr.attendance.job'
    _description = '自動結算打卡記錄'

    def hr_attendance_run(self):
        self.env['hr.attendance.check'].create_attendance()

