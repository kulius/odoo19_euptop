# -*- coding: utf-8 -*-
"""
Tests for overtime functionality
"""
from datetime import date, datetime, timedelta
from odoo.tests import tagged
from odoo.exceptions import UserError, ValidationError
from .common import SlHrmTestCommon


@tagged('post_install', '-at_install', 'sl_hrm', 'overtime')
class TestOvertimeType(SlHrmTestCommon):
    """Test overtime type model"""

    def test_overtime_type_created(self):
        """Test overtime type is created correctly"""
        self.assertEqual(self.overtime_type_normal.name, '平日加班')
        self.assertEqual(self.overtime_type_normal.time_type, 'half')

    def test_create_overtime_type(self):
        """Test creating a new overtime type"""
        ot_type = self.env['starrylord.overtime.type'].create({
            'name': '國定假日加班',
            'time_type': 'half',
            'date_type': 'holiday',
            'eight_hours': True,
        })
        self.assertTrue(ot_type.id)
        self.assertEqual(ot_type.name, '國定假日加班')


@tagged('post_install', '-at_install', 'sl_hrm', 'overtime')
class TestOvertimeTypeRule(SlHrmTestCommon):
    """Test overtime type rule model"""

    def test_overtime_rule_exists(self):
        """Test overtime rules are created"""
        rules = self.env['starrylord.overtime.type.rule'].search([
            ('rule_id', '=', self.overtime_type_normal.id)
        ])
        self.assertTrue(len(rules) >= 2)

    def test_overtime_rule_rates(self):
        """Test overtime rule rates"""
        rule_2hr = self.env['starrylord.overtime.type.rule'].search([
            ('rule_id', '=', self.overtime_type_normal.id),
            ('time', '=', 2)
        ], limit=1)
        self.assertEqual(rule_2hr.rate, 1.34)

    def test_create_overtime_rule(self):
        """Test creating overtime rules"""
        # Create holiday overtime type
        ot_holiday = self.env['starrylord.overtime.type'].create({
            'name': '假日加班測試',
            'time_type': 'half',
            'date_type': 'day_off',
            'eight_hours': True,
        })

        # Create rules for holiday overtime
        self.env['starrylord.overtime.type.rule'].create({
            'rule_id': ot_holiday.id,
            'name': '前8小時',
            'time': 8,
            'rate': 1.34,
        })
        self.env['starrylord.overtime.type.rule'].create({
            'rule_id': ot_holiday.id,
            'name': '8小時後',
            'time': 12,
            'rate': 1.67,
        })

        rules = self.env['starrylord.overtime.type.rule'].search([
            ('rule_id', '=', ot_holiday.id)
        ])
        self.assertEqual(len(rules), 2)


@tagged('post_install', '-at_install', 'sl_hrm', 'overtime')
class TestOvertimeApply(SlHrmTestCommon):
    """Test overtime application model"""

    def test_overtime_apply_model_exists(self):
        """Test that overtime apply model exists"""
        model_exists = 'starrylord.overtime.apply' in self.env
        self.assertTrue(model_exists)

    def test_overtime_apply_has_required_fields(self):
        """Test that overtime apply model has required fields"""
        model = self.env['starrylord.overtime.apply']
        # Check key fields exist
        self.assertIn('employee_id', model._fields)
        self.assertIn('overtime_type_id', model._fields)
        self.assertIn('start_day', model._fields)
        self.assertIn('hour_from', model._fields)
        self.assertIn('hour_to', model._fields)
        self.assertIn('state', model._fields)

    def test_overtime_type_assignment(self):
        """Test that overtime types are created correctly"""
        self.assertTrue(self.overtime_type_normal)
        self.assertTrue(self.overtime_type_holiday)


@tagged('post_install', '-at_install', 'sl_hrm', 'overtime')
class TestOvertimeWorkflow(SlHrmTestCommon):
    """Test overtime workflow"""

    def test_overtime_state_field(self):
        """Test overtime application state field exists"""
        model = self.env['starrylord.overtime.apply']
        self.assertIn('state', model._fields)

        # Check the selection values
        state_field = model._fields['state']
        self.assertTrue(state_field.selection)
