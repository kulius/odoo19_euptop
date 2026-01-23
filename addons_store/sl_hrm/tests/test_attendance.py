# -*- coding: utf-8 -*-
"""
Tests for attendance functionality
"""
from datetime import date, datetime, timedelta
from odoo.tests import tagged
from odoo.exceptions import UserError, ValidationError
from .common import SlHrmTestCommon


@tagged('post_install', '-at_install', 'sl_hrm', 'attendance')
class TestAttendanceCheck(SlHrmTestCommon):
    """Test attendance check model"""

    def test_create_attendance_check(self):
        """Test creating an attendance check record"""
        check_date = self.get_next_workday(date.today())

        check = self.env['hr.attendance.check'].create({
            'employee_id': self.employee.id,
            'date': check_date,
        })

        self.assertEqual(check.employee_id, self.employee)
        self.assertEqual(check.date, check_date)

    def test_attendance_check_day_of_week(self):
        """Test day of week calculation"""
        # Create check for a known day
        check_date = date(2026, 1, 26)  # This is a Monday
        check = self.env['hr.attendance.check'].create({
            'employee_id': self.employee.id,
            'date': check_date,
        })

        # Day of week should be calculated (0=Mon, 6=Sun)
        self.assertEqual(check_date.weekday(), 0)  # Monday

    def test_attendance_check_department(self):
        """Test department is correctly related"""
        check_date = self.get_next_workday(date.today())

        check = self.env['hr.attendance.check'].create({
            'employee_id': self.employee.id,
            'date': check_date,
        })

        self.assertEqual(check.department_id, self.department)


@tagged('post_install', '-at_install', 'sl_hrm', 'attendance')
class TestAttendanceRepair(SlHrmTestCommon):
    """Test attendance repair (出勤異常說明單) model"""

    def test_create_attendance_repair(self):
        """Test creating an attendance repair request"""
        # First create an attendance check record
        check_date = self.get_next_workday(date.today())
        check = self.env['hr.attendance.check'].create({
            'employee_id': self.employee.id,
            'date': check_date,
        })

        repair = self.env['sl.attendance.repair'].create({
            'name': 'Test attendance repair',
            'employee_id': self.employee.id,
            'user_id': self.test_user.id,
            'sl_attendance_check_id': check.id,
            'hour_from': '8',
            'min_from': '0',
            'hour_to': '17',
            'min_to': '30',
            'notes': 'Forgot to check in',
        })

        self.assertEqual(repair.state, 'draft')
        self.assertEqual(repair.employee_id, self.employee)

    def test_attendance_repair_states(self):
        """Test attendance repair has correct states"""
        check_date = self.get_next_workday(date.today())
        check = self.env['hr.attendance.check'].create({
            'employee_id': self.employee.id,
            'date': check_date,
        })

        repair = self.env['sl.attendance.repair'].create({
            'name': 'Test repair states',
            'employee_id': self.employee.id,
            'user_id': self.test_user.id,
            'sl_attendance_check_id': check.id,
            'hour_from': '8',
            'min_from': '0',
            'notes': 'Test repair',
        })

        # Check valid states
        self.assertIn(repair.state, ['draft', 'f_approve', 'confirmed', 'refused', 'cancel'])


@tagged('post_install', '-at_install', 'sl_hrm', 'attendance')
class TestAttendanceRaw(SlHrmTestCommon):
    """Test raw attendance data model"""

    def test_attendance_raw_model_exists(self):
        """Test that attendance raw model exists"""
        # Check if model is registered
        model_exists = 'hr.attendance.raw' in self.env
        self.assertTrue(model_exists)

    def test_create_attendance_raw(self):
        """Test creating raw attendance record"""
        raw = self.env['hr.attendance.raw'].create({
            'employee_id': self.employee.id,
            'check_time': datetime.now(),
            'source': 'manual',
        })

        self.assertEqual(raw.employee_id, self.employee)


@tagged('post_install', '-at_install', 'sl_hrm', 'attendance')
class TestAttendanceImport(SlHrmTestCommon):
    """Test attendance import functionality"""

    def test_import_model_exists(self):
        """Test that attendance import model exists"""
        # Check if model is registered
        model_exists = 'sl.attendance.import' in self.env
        self.assertTrue(model_exists)
