# -*- coding: utf-8 -*-
"""
Tests for employee functionality
"""
from datetime import date, datetime, timedelta
from odoo.tests import tagged
from odoo.exceptions import UserError, ValidationError
from .common import SlHrmTestCommon


@tagged('post_install', '-at_install', 'sl_hrm', 'employee')
class TestEmployee(SlHrmTestCommon):
    """Test employee model extensions"""

    def test_employee_created(self):
        """Test employee is created correctly"""
        self.assertEqual(self.employee.name, 'Test Employee')
        # Employee number is auto-generated based on company prefix + year + sequence
        self.assertTrue(self.employee.employee_number)
        self.assertEqual(self.employee.department_id, self.department)

    def test_employee_schedule(self):
        """Test employee has schedule assigned"""
        self.assertEqual(self.employee.schedule_id, self.schedule)

    def test_employee_manager(self):
        """Test employee has manager assigned"""
        self.assertEqual(self.employee.parent_id, self.manager)

    def test_create_employee(self):
        """Test creating a new employee"""
        employee = self.env['hr.employee'].create({
            'name': 'New Employee',
            'employee_number': 'NEW001',
            'department_id': self.department.id,
            'company_id': self.company.id,
            'gender': 'female',
        })

        self.assertTrue(employee.id)
        self.assertEqual(employee.name, 'New Employee')

    def test_employee_gender(self):
        """Test employee gender field"""
        self.assertEqual(self.employee.gender, 'male')

        # Create female employee
        female_emp = self.env['hr.employee'].create({
            'name': 'Female Employee',
            'employee_number': 'FEM001',
            'gender': 'female',
            'company_id': self.company.id,
        })
        self.assertEqual(female_emp.gender, 'female')


@tagged('post_install', '-at_install', 'sl_hrm', 'employee')
class TestEmployeeNumber(SlHrmTestCommon):
    """Test employee number functionality"""

    def test_employee_number_unique(self):
        """Test employee number is auto-generated and set"""
        self.assertTrue(self.employee.employee_number)
        # Employee number is auto-generated, just verify it exists and is not empty
        self.assertGreater(len(self.employee.employee_number), 0)

    def test_employee_number_search(self):
        """Test searching by employee number"""
        # Search using the actual auto-generated employee number
        found = self.env['hr.employee'].search([
            ('employee_number', '=', self.employee.employee_number)
        ])
        self.assertEqual(len(found), 1)
        self.assertEqual(found, self.employee)


@tagged('post_install', '-at_install', 'sl_hrm', 'employee')
class TestDepartment(SlHrmTestCommon):
    """Test department model"""

    def test_department_created(self):
        """Test department is created correctly"""
        self.assertEqual(extract_name(self.department.name), 'Test Department')

    def test_department_company(self):
        """Test department has company"""
        self.assertEqual(self.department.company_id, self.company)

    def test_create_department(self):
        """Test creating a new department"""
        dept = self.env['hr.department'].create({
            'name': 'New Department',
            'company_id': self.company.id,
        })
        self.assertTrue(dept.id)


@tagged('post_install', '-at_install', 'sl_hrm', 'employee')
class TestEmployeePublic(SlHrmTestCommon):
    """Test employee public model"""

    def test_employee_public_model_exists(self):
        """Test employee public model exists"""
        # Check if model is registered
        model_exists = 'hr.employee.public' in self.env
        self.assertTrue(model_exists)


@tagged('post_install', '-at_install', 'sl_hrm', 'employee')
class TestEmployeeSubstitute(SlHrmTestCommon):
    """Test employee substitute functionality"""

    def test_substitute_field(self):
        """Test substitute field exists"""
        # substitute_id should be available
        self.assertTrue(hasattr(self.employee, 'substitute_id'))


def extract_name(name_val):
    """Extract string name from JSONB value"""
    if isinstance(name_val, dict):
        return name_val.get('zh_TW') or name_val.get('en_US') or str(name_val)
    return str(name_val) if name_val else ''
