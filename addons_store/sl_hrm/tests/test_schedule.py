# -*- coding: utf-8 -*-
"""
Tests for schedule and personal calendar functionality
"""
from datetime import date, datetime, timedelta
from odoo.tests import tagged
from odoo.exceptions import UserError, ValidationError
from .common import SlHrmTestCommon


@tagged('post_install', '-at_install', 'sl_hrm', 'schedule')
class TestSchedule(SlHrmTestCommon):
    """Test schedule model"""

    def test_schedule_created(self):
        """Test schedule is created correctly"""
        self.assertEqual(self.schedule.name, 'Standard Schedule')
        self.assertFalse(self.schedule.is_user_personal_calendar)
        self.assertTrue(self.schedule.is_control_personal_calendar)

    def test_create_schedule(self):
        """Test creating a new schedule"""
        schedule = self.env['hr.schedule'].create({
            'name': 'Night Shift',
            'is_user_personal_calendar': False,
            'is_control_personal_calendar': True,
        })

        self.assertTrue(schedule.id)
        self.assertEqual(schedule.name, 'Night Shift')

    def test_schedule_has_worktimes(self):
        """Test schedule has worktime entries"""
        worktimes = self.env['hr.schedule.worktime'].search([
            ('worktime_id', '=', self.schedule.id)
        ])
        self.assertEqual(len(worktimes), 7)  # 7 days of the week


@tagged('post_install', '-at_install', 'sl_hrm', 'schedule')
class TestScheduleWorktime(SlHrmTestCommon):
    """Test schedule worktime model"""

    def test_worktime_days(self):
        """Test worktime covers all days of week"""
        worktimes = self.env['hr.schedule.worktime'].search([
            ('worktime_id', '=', self.schedule.id)
        ])

        days = [w.dayofweek for w in worktimes]
        expected_days = ['0', '1', '2', '3', '4', '5', '6']

        for day in expected_days:
            self.assertIn(day, days)

    def test_worktime_hours(self):
        """Test worktime hours for workdays"""
        monday = self.env['hr.schedule.worktime'].search([
            ('worktime_id', '=', self.schedule.id),
            ('dayofweek', '=', '0')  # Monday
        ], limit=1)

        self.assertEqual(monday.am_start, 8.0)
        self.assertEqual(monday.pm_end, 17.5)

    def test_worktime_day_off(self):
        """Test day off configuration"""
        saturday = self.env['hr.schedule.worktime'].search([
            ('worktime_id', '=', self.schedule.id),
            ('dayofweek', '=', '5')  # Saturday
        ], limit=1)

        self.assertEqual(saturday.date_type, 'day_off')

    def test_create_worktime(self):
        """Test creating new worktime entry"""
        new_schedule = self.env['hr.schedule'].create({
            'name': 'Custom Schedule',
        })

        worktime = self.env['hr.schedule.worktime'].create({
            'worktime_id': new_schedule.id,
            'name': 'Monday Custom',
            'dayofweek': '0',
            'date_type': 'schedule',
            'type': 'schedule',
            'am_start': 9.0,
            'am_end': 12.0,
            'pm_start': 13.0,
            'pm_end': 18.0,
            'work_start': 9.0,
            'work_end': 18.0,
            'sequence': 0,
        })

        self.assertEqual(worktime.am_start, 9.0)
        self.assertEqual(worktime.work_end, 18.0)


@tagged('post_install', '-at_install', 'sl_hrm', 'schedule')
class TestPersonalCalendar(SlHrmTestCommon):
    """Test personal calendar model"""

    def test_personal_calendar_model_exists(self):
        """Test personal calendar model exists"""
        model_exists = 'hr.personal.calendar' in self.env
        self.assertTrue(model_exists)

    def test_create_personal_calendar_entry(self):
        """Test creating personal calendar entry"""
        entry_date = self.get_next_workday(date.today())

        entry = self.env['hr.personal.calendar'].create({
            'employee_id': self.employee.id,
            'calendar_date': entry_date,
            'schedule_id': self.schedule.id,
            'date_type': 'schedule',
        })

        # Compare IDs since employee_id might return hr.employee.public
        self.assertEqual(entry.employee_id.id, self.employee.id)
        self.assertEqual(entry.calendar_date, entry_date)

    def test_personal_calendar_holiday(self):
        """Test personal calendar with holiday type"""
        entry_date = self.get_next_workday(date.today() + timedelta(days=7))

        entry = self.env['hr.personal.calendar'].create({
            'employee_id': self.employee.id,
            'calendar_date': entry_date,
            'schedule_id': self.schedule.id,
            'date_type': 'leave',
        })

        self.assertEqual(entry.date_type, 'leave')


@tagged('post_install', '-at_install', 'sl_hrm', 'schedule')
class TestScheduleCalculation(SlHrmTestCommon):
    """Test schedule calculation methods"""

    def test_employee_has_schedule(self):
        """Test employee has schedule assigned"""
        self.assertTrue(self.employee.schedule_id)
        self.assertEqual(self.employee.schedule_id, self.schedule)

    def test_schedule_worktime_lookup(self):
        """Test looking up worktime for a specific day"""
        # Get Monday's worktime
        monday_worktime = self.env['hr.schedule.worktime'].search([
            ('worktime_id', '=', self.schedule.id),
            ('dayofweek', '=', '0')
        ], limit=1)

        self.assertTrue(monday_worktime)
        self.assertEqual(monday_worktime.date_type, 'schedule')
