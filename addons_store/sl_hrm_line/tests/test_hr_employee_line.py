# -*- coding: utf-8 -*-

from odoo.tests import TransactionCase, tagged
from odoo.exceptions import ValidationError
from psycopg2 import IntegrityError


@tagged('post_install', '-at_install', 'sl_hrm_line')
class TestHrEmployeeLine(TransactionCase):
    """測試員工 LINE 綁定功能"""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # 建立測試部門
        cls.department = cls.env['hr.department'].create({
            'name': 'Test Department LINE',
        })
        # 建立測試員工
        cls.employee = cls.env['hr.employee'].create({
            'name': '測試員工 LINE',
            'department_id': cls.department.id,
            'work_email': 'test_line@example.com',
        })
        cls.employee2 = cls.env['hr.employee'].create({
            'name': '測試員工二 LINE',
            'department_id': cls.department.id,
        })

    def test_01_line_binding(self):
        """測試 LINE 帳號綁定"""
        # 初始狀態應為未綁定
        self.assertFalse(self.employee.is_line_bound)
        self.assertFalse(self.employee.line_user_id)

        # 綁定 LINE 帳號
        self.employee.write({
            'line_user_id': 'U1234567890abcdef',
            'line_display_name': 'Test User',
            'line_picture_url': 'https://example.com/picture.jpg',
        })

        # 驗證綁定結果
        self.assertTrue(self.employee.is_line_bound)
        self.assertEqual(self.employee.line_user_id, 'U1234567890abcdef')
        self.assertEqual(self.employee.line_display_name, 'Test User')

    def test_02_line_unbinding(self):
        """測試解除 LINE 綁定"""
        # 先綁定
        self.employee.write({
            'line_user_id': 'U1234567890abcdef',
            'line_display_name': 'Test User',
            'line_picture_url': 'https://example.com/picture.jpg',
        })
        self.assertTrue(self.employee.is_line_bound)

        # 解除綁定
        self.employee.action_unbind_line()

        # 驗證解除綁定結果
        self.assertFalse(self.employee.is_line_bound)
        self.assertFalse(self.employee.line_user_id)
        self.assertFalse(self.employee.line_display_name)
        self.assertFalse(self.employee.line_picture_url)
        self.assertFalse(self.employee.line_binding_date)

    def test_03_duplicate_line_user_id(self):
        """測試重複 LINE ID 驗證 (SQL 約束)"""
        # 綁定第一個員工
        self.employee.write({
            'line_user_id': 'U_duplicate_test',
        })

        # 嘗試用相同 LINE ID 綁定第二個員工應該失敗
        with self.assertRaises(IntegrityError):
            with self.cr.savepoint():
                self.employee2.write({
                    'line_user_id': 'U_duplicate_test',
                })

    def test_04_get_employee_by_line_user_id(self):
        """測試透過 LINE ID 查詢員工"""
        line_user_id = 'U_search_test_123'
        self.employee.write({'line_user_id': line_user_id})

        # 查詢存在的 LINE ID
        found = self.env['hr.employee'].get_employee_by_line_user_id(line_user_id)
        self.assertEqual(found.id, self.employee.id)

        # 查詢不存在的 LINE ID
        not_found = self.env['hr.employee'].get_employee_by_line_user_id('U_not_exist')
        self.assertFalse(not_found)

        # 查詢空值
        empty = self.env['hr.employee'].get_employee_by_line_user_id('')
        self.assertFalse(empty)

    def test_05_get_employee_data(self):
        """測試取得員工 API 資料格式"""
        self.employee.write({
            'line_user_id': 'U_api_data_test',
            'line_display_name': 'API Test User',
            'line_picture_url': 'https://example.com/api_pic.jpg',
        })

        data = self.employee._get_employee_data()

        # 驗證資料結構
        self.assertIn('id', data)
        self.assertIn('employee_id', data)
        self.assertIn('name', data)
        self.assertIn('department', data)
        self.assertIn('line_user_id', data)
        self.assertIn('line_display_name', data)
        self.assertIn('picture_url', data)

        # 驗證資料內容
        self.assertEqual(data['id'], self.employee.id)
        self.assertEqual(data['name'], '測試員工 LINE')
        self.assertEqual(data['department'], 'Test Department LINE')
        self.assertEqual(data['line_user_id'], 'U_api_data_test')
        self.assertEqual(data['line_display_name'], 'API Test User')
