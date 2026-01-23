# -*- coding: utf-8 -*-
"""
Common test utilities for sl_hrm module
"""
from datetime import date, datetime, timedelta
from odoo.tests import TransactionCase, tagged


class SlHrmTestCommon(TransactionCase):
    """Common setup for sl_hrm tests"""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        # Create test company
        cls.company = cls.env['res.company'].create({
            'name': 'Test Company',
        })

        # Create test department
        cls.department = cls.env['hr.department'].create({
            'name': 'Test Department',
            'company_id': cls.company.id,
        })

        # Create schedule
        cls.schedule = cls.env['hr.schedule'].create({
            'name': 'Standard Schedule',
            'is_user_personal_calendar': False,
            'is_control_personal_calendar': True,
        })

        # Create schedule worktime (Mon-Fri 08:00-17:30)
        for day in range(5):  # Monday to Friday
            cls.env['hr.schedule.worktime'].create({
                'worktime_id': cls.schedule.id,
                'name': f'Workday {day}',
                'dayofweek': str(day),
                'date_type': 'schedule',
                'type': 'schedule',
                'am_start': 8.0,
                'am_end': 12.0,
                'pm_start': 13.0,
                'pm_end': 17.5,
                'work_start': 8.0,
                'work_end': 17.5,
                'sequence': day,
            })

        # Saturday - day off
        cls.env['hr.schedule.worktime'].create({
            'worktime_id': cls.schedule.id,
            'name': 'Saturday',
            'dayofweek': '5',
            'date_type': 'day_off',
            'type': 'day_off',
            'sequence': 5,
        })

        # Sunday - regular holiday
        cls.env['hr.schedule.worktime'].create({
            'worktime_id': cls.schedule.id,
            'name': 'Sunday',
            'dayofweek': '6',
            'date_type': 'regular_holiday',
            'type': 'regular_holiday',
            'sequence': 6,
        })

        # Create test user
        cls.test_user = cls.env['res.users'].create({
            'name': 'Test Employee User',
            'login': 'test_emp_user',
            'email': 'test_emp@test.com',
            'company_id': cls.company.id,
            'company_ids': [(4, cls.company.id)],
        })

        # Create test employee
        cls.employee = cls.env['hr.employee'].create({
            'name': 'Test Employee',
            'employee_number': 'TEST001',
            'department_id': cls.department.id,
            'company_id': cls.company.id,
            'user_id': cls.test_user.id,
            'schedule_id': cls.schedule.id,
            'gender': 'male',
        })

        # Create manager user
        cls.manager_user = cls.env['res.users'].create({
            'name': 'Test Manager',
            'login': 'test_manager',
            'email': 'test_manager@test.com',
            'company_id': cls.company.id,
            'company_ids': [(4, cls.company.id)],
        })

        # Create manager employee
        cls.manager = cls.env['hr.employee'].create({
            'name': 'Test Manager',
            'employee_number': 'MGR001',
            'department_id': cls.department.id,
            'company_id': cls.company.id,
            'user_id': cls.manager_user.id,
            'schedule_id': cls.schedule.id,
            'gender': 'male',
        })

        # Set manager as parent
        cls.employee.parent_id = cls.manager.id

        # Create holiday types
        cls.holiday_type_annual = cls.env['starrylord.holiday.type'].create({
            'name': '特休',
            'request_unit': 'hour',
            'is_distribute': True,
        })

        cls.holiday_type_sick = cls.env['starrylord.holiday.type'].create({
            'name': '病假',
            'request_unit': 'hour',
            'is_distribute': True,
        })

        cls.holiday_type_personal = cls.env['starrylord.holiday.type'].create({
            'name': '事假',
            'request_unit': 'hour',
            'is_distribute': False,
        })

        # Create overtime types
        cls.overtime_type_normal = cls.env['starrylord.overtime.type'].create({
            'name': '平日加班',
            'time_type': 'half',
            'date_type': 'schedule',
            'eight_hours': True,
        })

        cls.overtime_type_holiday = cls.env['starrylord.overtime.type'].create({
            'name': '休假日加班',
            'time_type': 'half',
            'date_type': 'day_off',
            'eight_hours': True,
        })

        # Create overtime type rules
        cls.env['starrylord.overtime.type.rule'].create({
            'rule_id': cls.overtime_type_normal.id,
            'name': '前2小時',
            'time': 2,
            'rate': 1.34,
        })
        cls.env['starrylord.overtime.type.rule'].create({
            'rule_id': cls.overtime_type_normal.id,
            'name': '2小時後',
            'time': 8,
            'rate': 1.67,
        })

        # Create hour and minute lists (only if not exist)
        for hour in range(8, 19):
            existing = cls.env['starrylord.holiday.hour.list'].search([('hour', '=', hour)], limit=1)
            if not existing:
                cls.env['starrylord.holiday.hour.list'].create({
                    'name': str(hour),
                    'hour': hour,
                })

        for minute in [0, 30]:
            existing = cls.env['starrylord.holiday.min.list'].search([('minute', '=', minute)], limit=1)
            if not existing:
                cls.env['starrylord.holiday.min.list'].create({
                    'name': f'{minute:02d}',
                    'minute': minute,
                })

        # Create holiday allocation for test employee
        cls.allocation_annual = cls.env['starrylord.holiday.allocation'].create({
            'employee_id': cls.employee.id,
            'holiday_type_id': cls.holiday_type_annual.id,
            'year': str(date.today().year),
            'time_type': 'hour',
            'distribute_time': 80.0,  # 80 hours = 10 days
            'duration_time': 80,
            'duration_date': 10,
            'validity_start': date(date.today().year, 1, 1),
            'validity_end': date(date.today().year, 12, 31),
        })

        cls.allocation_sick = cls.env['starrylord.holiday.allocation'].create({
            'employee_id': cls.employee.id,
            'holiday_type_id': cls.holiday_type_sick.id,
            'year': str(date.today().year),
            'time_type': 'hour',
            'distribute_time': 30.0,  # 30 hours
            'duration_time': 30,
            'duration_date': 3,
            'validity_start': date(date.today().year, 1, 1),
            'validity_end': date(date.today().year, 12, 31),
        })

    def get_next_workday(self, from_date=None):
        """Get the next workday (Monday-Friday) from given date"""
        if from_date is None:
            from_date = date.today()

        # Ensure it's a workday (Mon=0 to Fri=4)
        while from_date.weekday() > 4:
            from_date += timedelta(days=1)

        return from_date
