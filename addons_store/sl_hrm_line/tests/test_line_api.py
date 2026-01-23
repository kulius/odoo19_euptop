# -*- coding: utf-8 -*-

from odoo.tests import HttpCase, tagged
import json


@tagged('post_install', '-at_install', 'sl_hrm_line')
class TestLineAPI(HttpCase):
    """測試 LINE REST API"""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # 建立測試部門
        cls.department = cls.env['hr.department'].create({
            'name': 'API Test Dept',
        })
        # 建立未綁定員工
        cls.employee_unbound = cls.env['hr.employee'].create({
            'name': 'API 測試員工',
            'department_id': cls.department.id,
        })
        # 建立已綁定員工
        cls.employee_bound = cls.env['hr.employee'].create({
            'name': 'API 已綁定員工',
            'department_id': cls.department.id,
            'line_user_id': 'U_api_bound_test',
            'line_display_name': 'Bound User',
        })
        # 測試座標
        cls.test_lat = 25.0339639
        cls.test_lng = 121.5644722

    def _make_request(self, url, method='GET', data=None, headers=None):
        """發送 HTTP 請求"""
        if headers is None:
            headers = {}
        headers['Content-Type'] = 'application/json'

        if method == 'POST':
            response = self.url_open(
                url,
                data=json.dumps(data) if data else None,
                headers=headers
            )
        else:
            response = self.url_open(url, headers=headers)

        return response

    def test_01_check_binding_not_bound(self):
        """測試檢查綁定 - 未綁定"""
        response = self.url_open(
            '/api/line/check-binding',
            data=json.dumps({
                'userId': 'U_new_user_not_bound',
                'displayName': 'New User',
                'pictureUrl': 'https://example.com/pic.jpg'
            }),
            headers={'Content-Type': 'application/json'}
        )

        self.assertEqual(response.status_code, 200)
        result = json.loads(response.content)
        self.assertTrue(result['success'])
        self.assertFalse(result['isBound'])
        self.assertIsNone(result['data'])

    def test_02_check_binding_bound(self):
        """測試檢查綁定 - 已綁定"""
        response = self.url_open(
            '/api/line/check-binding',
            data=json.dumps({
                'userId': 'U_api_bound_test',
                'displayName': 'Updated Name',
                'pictureUrl': 'https://example.com/new_pic.jpg'
            }),
            headers={'Content-Type': 'application/json'}
        )

        self.assertEqual(response.status_code, 200)
        result = json.loads(response.content)
        self.assertTrue(result['success'])
        self.assertTrue(result['isBound'])
        self.assertIsNotNone(result['data'])
        self.assertEqual(result['data']['name'], 'API 已綁定員工')

    def test_03_check_binding_missing_user_id(self):
        """測試檢查綁定 - 缺少 LINE User ID"""
        response = self.url_open(
            '/api/line/check-binding',
            data=json.dumps({
                'displayName': 'Test User'
            }),
            headers={'Content-Type': 'application/json'}
        )

        self.assertEqual(response.status_code, 400)
        result = json.loads(response.content)
        self.assertFalse(result['success'])
        self.assertEqual(result['error']['code'], 'MISSING_USER_ID')

    def test_04_bind_employee_success(self):
        """測試綁定成功"""
        response = self.url_open(
            '/api/line/bind',
            data=json.dumps({
                'line_user_id': 'U_new_bind_test',
                'line_display_name': 'New Bind User',
                'line_picture_url': 'https://example.com/pic.jpg',
                'employee_name': 'API 測試員工'
            }),
            headers={'Content-Type': 'application/json'}
        )

        self.assertEqual(response.status_code, 200)
        result = json.loads(response.content)
        self.assertTrue(result['success'])
        self.assertTrue(result['data']['matched'])
        self.assertEqual(result['data']['name'], 'API 測試員工')

        # 驗證資料庫
        self.employee_unbound.invalidate_recordset()
        self.assertEqual(self.employee_unbound.line_user_id, 'U_new_bind_test')

    def test_05_bind_employee_not_found(self):
        """測試綁定 - 找不到員工"""
        response = self.url_open(
            '/api/line/bind',
            data=json.dumps({
                'line_user_id': 'U_not_found_test',
                'line_display_name': 'Not Found User',
                'employee_name': '不存在的員工名稱'
            }),
            headers={'Content-Type': 'application/json'}
        )

        self.assertEqual(response.status_code, 200)
        result = json.loads(response.content)
        self.assertTrue(result['success'])
        self.assertFalse(result['data']['matched'])

    def test_06_bind_employee_already_bound(self):
        """測試綁定 - LINE 帳號已綁定"""
        response = self.url_open(
            '/api/line/bind',
            data=json.dumps({
                'line_user_id': 'U_api_bound_test',  # 已經綁定的 LINE ID
                'line_display_name': 'Already Bound',
                'employee_name': 'Some Employee'
            }),
            headers={'Content-Type': 'application/json'}
        )

        self.assertEqual(response.status_code, 400)
        result = json.loads(response.content)
        self.assertFalse(result['success'])
        self.assertEqual(result['error']['code'], 'ALREADY_BOUND')

    def test_07_get_user_success(self):
        """測試取得用戶資料"""
        response = self.url_open(
            '/api/line/user',
            headers={
                'Content-Type': 'application/json',
                'X-Line-User-Id': 'U_api_bound_test'
            }
        )

        self.assertEqual(response.status_code, 200)
        result = json.loads(response.content)
        self.assertTrue(result['success'])
        self.assertEqual(result['data']['name'], 'API 已綁定員工')

    def test_08_get_user_not_found(self):
        """測試取得用戶資料 - 未綁定"""
        response = self.url_open(
            '/api/line/user',
            headers={
                'Content-Type': 'application/json',
                'X-Line-User-Id': 'U_not_exist_user'
            }
        )

        self.assertEqual(response.status_code, 404)
        result = json.loads(response.content)
        self.assertFalse(result['success'])
        self.assertEqual(result['error']['code'], 'USER_NOT_FOUND')

    def test_09_get_user_missing_header(self):
        """測試取得用戶資料 - 缺少 Header"""
        response = self.url_open(
            '/api/line/user',
            headers={'Content-Type': 'application/json'}
        )

        self.assertEqual(response.status_code, 401)
        result = json.loads(response.content)
        self.assertFalse(result['success'])
        self.assertEqual(result['error']['code'], 'MISSING_USER_ID')

    def test_10_attendance_today_success(self):
        """測試今日打卡狀態"""
        response = self.url_open(
            '/api/line/attendance/today',
            headers={
                'Content-Type': 'application/json',
                'X-Line-User-Id': 'U_api_bound_test'
            }
        )

        self.assertEqual(response.status_code, 200)
        result = json.loads(response.content)
        self.assertTrue(result['success'])
        self.assertIn('status', result['data'])

    def test_11_clock_in_success(self):
        """測試打卡 API"""
        # 清除既有打卡記錄
        self.env['hr.attendance'].search([
            ('employee_id', '=', self.employee_bound.id)
        ]).unlink()

        response = self.url_open(
            '/api/line/attendance/clock',
            data=json.dumps({
                'type': 'in',
                'latitude': self.test_lat,
                'longitude': self.test_lng,
                'accuracy': 10
            }),
            headers={
                'Content-Type': 'application/json',
                'X-Line-User-Id': 'U_api_bound_test'
            }
        )

        self.assertEqual(response.status_code, 200)
        result = json.loads(response.content)
        self.assertTrue(result['success'])
        self.assertEqual(result['data']['type'], 'in')
        self.assertEqual(result['data']['status'], 'clocked_in')

    def test_12_clock_invalid_type(self):
        """測試打卡 API - 無效類型"""
        response = self.url_open(
            '/api/line/attendance/clock',
            data=json.dumps({
                'type': 'invalid',
                'latitude': self.test_lat,
                'longitude': self.test_lng,
            }),
            headers={
                'Content-Type': 'application/json',
                'X-Line-User-Id': 'U_api_bound_test'
            }
        )

        self.assertEqual(response.status_code, 400)
        result = json.loads(response.content)
        self.assertFalse(result['success'])
        self.assertEqual(result['error']['code'], 'INVALID_TYPE')

    def test_13_attendance_history(self):
        """測試出勤歷史 API"""
        response = self.url_open(
            '/api/line/attendance/history?limit=10&offset=0',
            headers={
                'Content-Type': 'application/json',
                'X-Line-User-Id': 'U_api_bound_test'
            }
        )

        self.assertEqual(response.status_code, 200)
        result = json.loads(response.content)
        self.assertTrue(result['success'])
        self.assertIn('records', result['data'])
        self.assertIn('total', result['data'])
