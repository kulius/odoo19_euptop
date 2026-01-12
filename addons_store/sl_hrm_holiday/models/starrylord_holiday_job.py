from odoo import api, fields, models, _
from odoo.exceptions import UserError
import datetime, logging
from dateutil.relativedelta import relativedelta

_logger = logging.getLogger(__name__)


class StarryLordHolidayJob(models.TransientModel):
    _name = 'starrylord.holiday.job'
    _description = '自動分配假別'

    # 分配生理假(每日批次處理)
    def holiday_menstrual_run(self, employee=False, year=''):
        holiday_menstrual = self.env['ir.config_parameter'].sudo().get_param('sl_hrm_holiday.holiday_menstrual_id', default=False)
        holiday_menstrual_id = self.env['starrylord.holiday.type'].sudo().search([('id', '=', int(holiday_menstrual))], limit=1)
        if not employee:
            executive_member = self.env['hr.employee'].sudo().search([('state', '=', 'working'), ('gender', '=', 'female')])
            #  .filtered(lambda x: x.state == 'working' and x.gender == 'female')
        else:
            executive_member = self.env['hr.employee'].sudo().search([('id', '=', employee), ('state', '=', 'working')], limit=1)

        if year == '':
            year = str(datetime.date.today().year)
        start_day = datetime.date.today() + relativedelta(day=1, month=1, year=int(year))
        end_day = start_day + relativedelta(month=12, day=31)
        for employee in executive_member:
            try:
                self.holiday_generate_function(year, holiday_menstrual_id, 3, 0, employee.id, start_day, end_day)
            except Exception as e:
                _logger.error('error on create holiday_menstrual %s',  repr(e))
                pass

    # 分配病假(每日批次處理)
    def holiday_sick_run(self, employee=False, year=''):
        holiday_sick = self.env['ir.config_parameter'].sudo().get_param('sl_hrm_holiday.holiday_sick_id', default=False)
        holiday_sick_id = self.env['starrylord.holiday.type'].sudo().search([('id', '=', int(holiday_sick))], limit=1)
        if not employee:
            executive_member = self.env['hr.employee'].sudo().search([('state', '=', 'working')])  # .filtered(lambda x: x.state == 'working')
        else:
            executive_member = self.env['hr.employee'].sudo().search([('id', '=', employee), ('state', '=', 'working')], limit=1)

        if year == '':
            year = str(datetime.date.today().year)
        start_day = datetime.date.today() + relativedelta(day=1, month=1, year=int(year))
        end_day = start_day + relativedelta(month=12, day=31)
        for employee in executive_member:
            try:
                self.holiday_generate_function(year, holiday_sick_id, 30, 0, employee.id, start_day, end_day)
            except Exception as e:
                _logger.error('error on create holiday_sick %s', repr(e))
                pass

    # 分配事假(每日批次處理)
    def holiday_leave_run(self, employee=False, year=''):
        holiday_leave = self.env['ir.config_parameter'].sudo().get_param('sl_hrm_holiday.holiday_leave_id', default=False)
        holiday_leave_id = self.env['starrylord.holiday.type'].sudo().search([('id', '=', int(holiday_leave))], limit=1)
        if not employee:
            executive_member = self.env['hr.employee'].sudo().search([('state', '=', 'working')])  # .filtered(lambda x: x.state == 'working')
        else:
            executive_member = self.env['hr.employee'].sudo().search([('id', '=', employee), ('state', '=', 'working')], limit=1)

        if year == '':
            year = str(datetime.date.today().year)
        start_day = datetime.date.today() + relativedelta(day=1, month=1, year=int(year))
        end_day = start_day + relativedelta(month=12, day=31)
        for employee in executive_member:
            try:
                self.holiday_generate_function(year, holiday_leave_id, 14, 0, employee.id, start_day, end_day)
            except Exception as e:
                _logger.error('error on create holiday_leave %s', repr(e))
                pass

    # 分配特休補遺(補過去紀錄)
    def holiday_special_run_makeup(self, date=False):
        if not date:
            raise UserError('請輸入要從哪天開始補!')

        today = datetime.date.today()
        loop_date = fields.Date.from_string(date)

        while loop_date <= today:
            self.holiday_special_run(date=loop_date)
            loop_date += relativedelta(days=1)

    # 分配特休(每日批次處理)
    def holiday_special_run(self, employee=False, date=False):
        # 特休制度
        cycle_calendar = self.env['ir.config_parameter'].sudo().get_param('sl_hrm_holiday.cycle_calendar', default=False)
        holiday_special = self.env['ir.config_parameter'].sudo().get_param('sl_hrm_holiday.holiday_special_id', default=False)
        holiday_special_id = self.env['starrylord.holiday.type'].sudo().search([('id', '=', int(holiday_special))], limit=1)
        if not date:
            year = str(datetime.date.today().year)
            date = datetime.date.today()
        else:
            if isinstance(date, str):
                date = fields.Date.from_string(date)
            year = str(date.year)
        if not employee:
            executive_member = self.env['hr.employee'].sudo().search([('state', '=', 'working')])   # .filtered(lambda x: x.state == 'working')
        else:
            executive_member = self.env['hr.employee'].sudo().search([('id', '=', employee), ('state', '=', 'working')], limit=1)
        if cycle_calendar == 'cycle':  # 週年制
            settings = self.env['starrylord.annual.leave.setting'].sudo().search([], order='seniority asc')
            if not settings:
                raise UserError('請設定年資特休對應表')
            for employee in executive_member:
                career_long = employee.job_tenure_return(date)  # 取得年資
                day, hour, tmp = 0, 0, False

                for rec in settings:  # 搜尋服務年資設定
                    if rec.seniority <= career_long:
                        day = rec.days  # 依服務年資給予的特休天數
                        tmp = rec
                        if rec.seniority == 0.5:
                            start_date = employee.registration_date + relativedelta(months=6)
                            t_year = str(employee.registration_date.year)
                        else:
                            start_date = employee.registration_date + relativedelta(year=int(year))
                            t_year = str((employee.registration_date + relativedelta(year=int(year))).year)
                        if tmp.annual_period < 0:
                            end_date = fields.Date.from_string(f"{int(t_year)}-12-31")
#                            end_date = fields.Date.from_string('2200-12-31')
                        else :
                            end_date = employee.registration_date + relativedelta(year=int(year),
                                                                                  months=tmp.annual_period,
                                                                                  days=-1)

                    else:
                        break
                try:
                    if day != 0 or hour != 0:
                        if start_date <= date:
                            self.holiday_generate_function(t_year, holiday_special_id, day, hour, employee.id,
                                                           start_date, end_date)
                except Exception as e:
                    _logger.error('error on create holiday_special %s', repr(e))
                    pass

        elif cycle_calendar == 'calendar':  # 歷年制
            start_day = datetime.date.today() + relativedelta(day=1, month=1, year=int(year))
            for employee in executive_member:
                career_long = employee.job_tenure_count if employee.job_tenure_count else 0
                day, hour, tmp = 0, 0, False
                for rec in self.env['starrylord.annual.leave.setting'].sudo().search([], order='seniority asc'):
                    if rec.seniority <= career_long:
                        day = rec.days
                        tmp = rec
                    else:
                        break
                try:
                    if day != 0 or hour != 0:
                        self.holiday_generate_function(year, holiday_special_id, day, hour, employee.id, start_day
                                                       , start_day + relativedelta(months=tmp.annual_period, days=-1))
                except Exception as e:
                    _logger.error('error on create holiday_special %s', repr(e))
                    pass

    def holiday_generate_function(self, year, h_type_id, day, hour, employee_id, start_day, end_day):
        holiday_table = self.env['starrylord.holiday.allocation']
        already_exists = holiday_table.search([('year', '=', year), ('duration_date', '=', day), ('holiday_type_id', '=', h_type_id.id), ('employee_id', '=', employee_id)])
        if not already_exists:
            holiday_table.create({
                'name': h_type_id.name,
                'year': year,
                'holiday_type_id': h_type_id.id,
                'duration_date': day,
                'duration_time': hour,
                'employee_id': employee_id,
                'validity_start': start_day,
                'validity_end': end_day,
            })
