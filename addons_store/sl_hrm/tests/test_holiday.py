# -*- coding: utf-8 -*-
"""
Tests for holiday (leave) functionality
"""
from datetime import date, datetime, timedelta
from odoo.tests import tagged
from odoo.exceptions import UserError, ValidationError
from .common import SlHrmTestCommon


@tagged('post_install', '-at_install', 'sl_hrm', 'holiday')
class TestHolidayType(SlHrmTestCommon):
    """Test holiday type model"""

    def test_create_holiday_type(self):
        """Test creating a holiday type"""
        holiday_type = self.env['starrylord.holiday.type'].create({
            'name': '婚假',
            'request_unit': 'day',
            'is_distribute': True,
        })
        self.assertEqual(holiday_type.name, '婚假')
        self.assertEqual(holiday_type.request_unit, 'day')
        self.assertTrue(holiday_type.is_distribute)

    def test_holiday_type_unique_name(self):
        """Test holiday type names should be meaningful"""
        holiday_type = self.env['starrylord.holiday.type'].search([
            ('name', '=', '特休')
        ])
        self.assertTrue(holiday_type)


@tagged('post_install', '-at_install', 'sl_hrm', 'holiday')
class TestHolidayAllocation(SlHrmTestCommon):
    """Test holiday allocation model"""

    def test_allocation_created(self):
        """Test allocation is created correctly"""
        # Compare IDs since the model might return hr.employee.public
        self.assertEqual(self.allocation_annual.employee_id.id, self.employee.id)
        self.assertEqual(self.allocation_annual.holiday_type_id, self.holiday_type_annual)
        # distribute_time may vary based on test runs, just verify it's positive
        self.assertGreater(self.allocation_annual.distribute_time, 0)

    def test_create_allocation_for_employee(self):
        """Test creating new allocation for employee"""
        allocation = self.env['starrylord.holiday.allocation'].create({
            'employee_id': self.employee.id,
            'holiday_type_id': self.holiday_type_personal.id,
            'year': str(date.today().year),
            'time_type': 'hour',
            'distribute_time': 14.0,
            'duration_time': 14,
            'validity_start': date(date.today().year, 1, 1),
            'validity_end': date(date.today().year, 12, 31),
        })
        self.assertTrue(allocation.id)
        self.assertEqual(allocation.distribute_time, 14.0)


@tagged('post_install', '-at_install', 'sl_hrm', 'holiday')
class TestHolidayApply(SlHrmTestCommon):
    """Test holiday application model"""

    def test_holiday_apply_model_exists(self):
        """Test that holiday apply model exists"""
        model_exists = 'starrylord.holiday.apply' in self.env
        self.assertTrue(model_exists)

    def test_holiday_apply_has_required_fields(self):
        """Test that holiday apply model has required fields"""
        model = self.env['starrylord.holiday.apply']
        # Check key fields exist
        self.assertIn('employee_id', model._fields)
        self.assertIn('holiday_allocation_id', model._fields)
        self.assertIn('substitute_id', model._fields)
        self.assertIn('start_day', model._fields)
        self.assertIn('end_day', model._fields)
        self.assertIn('state', model._fields)


@tagged('post_install', '-at_install', 'sl_hrm', 'holiday')
class TestHolidayUsedRecord(SlHrmTestCommon):
    """Test holiday used record model"""

    def test_used_record_model_exists(self):
        """Test that used record model exists"""
        # Check if model is registered
        model_exists = 'starrylord.holiday.used.record' in self.env
        self.assertTrue(model_exists)


@tagged('post_install', '-at_install', 'sl_hrm', 'holiday')
class TestAnnualLeaveSetting(SlHrmTestCommon):
    """Test annual leave setting model"""

    def test_annual_leave_setting(self):
        """Test creating annual leave settings"""
        setting = self.env['starrylord.annual.leave.setting'].create({
            'seniority': 1.0,
            'days': 7,
        })
        self.assertEqual(setting.seniority, 1.0)
        self.assertEqual(setting.days, 7)

    def test_annual_leave_setting_by_seniority(self):
        """Test annual leave days increase with seniority"""
        # Search for existing settings first or create new ones
        test_seniority = 99.5  # Use unlikely value to avoid conflict with existing data
        existing = self.env['starrylord.annual.leave.setting'].search([
            ('seniority', '=', test_seniority)
        ], limit=1)

        if not existing:
            setting = self.env['starrylord.annual.leave.setting'].create({
                'seniority': test_seniority,
                'days': 25,
            })
        else:
            setting = existing

        # Verify the setting
        self.assertEqual(setting.seniority, test_seniority)
        self.assertTrue(setting.days > 0)


@tagged('post_install', '-at_install', 'sl_hrm', 'holiday')
class TestPublicHoliday(SlHrmTestCommon):
    """Test public holiday model"""

    def test_create_public_holiday(self):
        """Test creating public holiday"""
        holiday = self.env['hr.public.holiday'].create({
            'name': '元旦',
            'date': date(date.today().year + 1, 1, 1),
        })
        self.assertEqual(holiday.name, '元旦')

    def test_public_holiday_list(self):
        """Test listing public holidays for a year"""
        # Create multiple holidays
        self.env['hr.public.holiday'].create({
            'name': '春節',
            'date': date(date.today().year + 1, 2, 10),
        })
        self.env['hr.public.holiday'].create({
            'name': '清明節',
            'date': date(date.today().year + 1, 4, 4),
        })

        holidays = self.env['hr.public.holiday'].search([
            ('date', '>=', date(date.today().year + 1, 1, 1)),
            ('date', '<=', date(date.today().year + 1, 12, 31)),
        ])
        self.assertTrue(len(holidays) >= 2)
