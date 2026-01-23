# -*- coding: utf-8 -*-

from odoo.tests import TransactionCase, tagged
from datetime import datetime, timedelta
import pytz


@tagged('post_install', '-at_install', 'sl_hrm_line')
class TestHrAttendanceLine(TransactionCase):
    """測試 GPS 打卡功能"""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # 建立測試部門
        cls.department = cls.env['hr.department'].create({
            'name': 'Test Attendance Dept',
        })
        # 建立測試員工
        cls.employee = cls.env['hr.employee'].create({
            'name': '打卡測試員工',
            'department_id': cls.department.id,
            'line_user_id': 'U_attendance_test',
        })
        # 測試座標 (台北 101)
        cls.test_lat = 25.0339639
        cls.test_lng = 121.5644722

    def setUp(self):
        super().setUp()
        # 每個測試前清除該員工的打卡記錄
        self.env['hr.attendance'].search([
            ('employee_id', '=', self.employee.id)
        ]).unlink()

    def test_01_clock_in(self):
        """測試上班打卡"""
        Attendance = self.env['hr.attendance']
        result = Attendance.clock_action(
            employee_id=self.employee.id,
            clock_type='in',
            latitude=self.test_lat,
            longitude=self.test_lng,
            accuracy=10
        )

        # 驗證回傳結果
        self.assertTrue(result['success'])
        self.assertEqual(result['data']['type'], 'in')
        self.assertEqual(result['data']['status'], 'clocked_in')
        self.assertEqual(result['data']['latitude'], self.test_lat)
        self.assertEqual(result['data']['longitude'], self.test_lng)

        # 驗證資料庫記錄
        attendance = Attendance.browse(result['data']['id'])
        self.assertEqual(attendance.employee_id.id, self.employee.id)
        self.assertEqual(attendance.in_latitude, self.test_lat)
        self.assertEqual(attendance.in_longitude, self.test_lng)
        self.assertFalse(attendance.check_out)

    def test_02_clock_out(self):
        """測試下班打卡"""
        Attendance = self.env['hr.attendance']

        # 先打上班卡
        clock_in_result = Attendance.clock_action(
            employee_id=self.employee.id,
            clock_type='in',
            latitude=self.test_lat,
            longitude=self.test_lng,
        )
        self.assertTrue(clock_in_result['success'])

        # 打下班卡 (不同座標)
        out_lat = 25.0478
        out_lng = 121.5170
        clock_out_result = Attendance.clock_action(
            employee_id=self.employee.id,
            clock_type='out',
            latitude=out_lat,
            longitude=out_lng,
        )

        # 驗證回傳結果
        self.assertTrue(clock_out_result['success'])
        self.assertEqual(clock_out_result['data']['type'], 'out')
        self.assertEqual(clock_out_result['data']['status'], 'clocked_out')

        # 驗證資料庫記錄
        attendance = Attendance.browse(clock_in_result['data']['id'])
        self.assertTrue(attendance.check_out)
        self.assertEqual(attendance.out_latitude, out_lat)
        self.assertEqual(attendance.out_longitude, out_lng)

    def test_03_duplicate_clock_in(self):
        """測試重複上班打卡驗證"""
        Attendance = self.env['hr.attendance']

        # 第一次上班打卡
        result1 = Attendance.clock_action(
            employee_id=self.employee.id,
            clock_type='in',
            latitude=self.test_lat,
            longitude=self.test_lng,
        )
        self.assertTrue(result1['success'])

        # 第二次上班打卡應該失敗
        result2 = Attendance.clock_action(
            employee_id=self.employee.id,
            clock_type='in',
            latitude=self.test_lat,
            longitude=self.test_lng,
        )
        self.assertFalse(result2['success'])
        self.assertEqual(result2['error']['code'], 'ALREADY_CLOCKED_IN')

    def test_04_clock_out_without_clock_in(self):
        """測試未打上班卡就打下班卡"""
        Attendance = self.env['hr.attendance']

        # 直接打下班卡應該失敗
        result = Attendance.clock_action(
            employee_id=self.employee.id,
            clock_type='out',
            latitude=self.test_lat,
            longitude=self.test_lng,
        )
        self.assertFalse(result['success'])
        self.assertEqual(result['error']['code'], 'NOT_CLOCKED_IN')

    def test_05_get_today_status_not_clocked(self):
        """測試取得今日打卡狀態 - 未打卡"""
        Attendance = self.env['hr.attendance']
        result = Attendance.get_today_status(self.employee.id)

        self.assertTrue(result['success'])
        self.assertEqual(result['data']['status'], 'not_clocked_in')
        self.assertIsNone(result['data']['check_in'])

    def test_06_get_today_status_clocked_in(self):
        """測試取得今日打卡狀態 - 已打上班卡"""
        Attendance = self.env['hr.attendance']

        # 打上班卡
        Attendance.clock_action(
            employee_id=self.employee.id,
            clock_type='in',
            latitude=self.test_lat,
            longitude=self.test_lng,
        )

        result = Attendance.get_today_status(self.employee.id)

        self.assertTrue(result['success'])
        self.assertEqual(result['data']['status'], 'clocked_in')
        self.assertIsNotNone(result['data']['check_in'])
        self.assertIsNone(result['data']['check_out'])
        self.assertEqual(result['data']['check_in_latitude'], self.test_lat)

    def test_07_get_today_status_clocked_out(self):
        """測試取得今日打卡狀態 - 已打下班卡"""
        Attendance = self.env['hr.attendance']

        # 打上班卡
        Attendance.clock_action(
            employee_id=self.employee.id,
            clock_type='in',
            latitude=self.test_lat,
            longitude=self.test_lng,
        )
        # 打下班卡
        Attendance.clock_action(
            employee_id=self.employee.id,
            clock_type='out',
            latitude=self.test_lat,
            longitude=self.test_lng,
        )

        result = Attendance.get_today_status(self.employee.id)

        self.assertTrue(result['success'])
        self.assertEqual(result['data']['status'], 'clocked_out')
        self.assertIsNotNone(result['data']['check_in'])
        self.assertIsNotNone(result['data']['check_out'])

    def test_08_get_attendance_history(self):
        """測試取得出勤歷史"""
        Attendance = self.env['hr.attendance']
        tz = pytz.timezone('Asia/Taipei')

        # 建立多筆歷史記錄
        for i in range(5):
            check_in = datetime.now(pytz.UTC) - timedelta(days=i+1, hours=9)
            check_out = check_in + timedelta(hours=8)
            Attendance.create({
                'employee_id': self.employee.id,
                'check_in': check_in.replace(tzinfo=None),
                'check_out': check_out.replace(tzinfo=None),
                'in_latitude': self.test_lat,
                'in_longitude': self.test_lng,
                'out_latitude': self.test_lat,
                'out_longitude': self.test_lng,
            })

        result = Attendance.get_attendance_history(
            employee_id=self.employee.id,
            limit=3,
            offset=0
        )

        self.assertTrue(result['success'])
        self.assertEqual(len(result['data']['records']), 3)
        self.assertEqual(result['data']['total'], 5)

        # 驗證記錄結構
        record = result['data']['records'][0]
        self.assertIn('id', record)
        self.assertIn('date', record)
        self.assertIn('weekday', record)
        self.assertIn('check_in', record)
        self.assertIn('check_out', record)
        self.assertIn('worked_hours', record)

    def test_09_invalid_clock_type(self):
        """測試無效的打卡類型"""
        Attendance = self.env['hr.attendance']
        result = Attendance.clock_action(
            employee_id=self.employee.id,
            clock_type='invalid',
            latitude=self.test_lat,
            longitude=self.test_lng,
        )
        self.assertFalse(result['success'])
        self.assertEqual(result['error']['code'], 'INVALID_TYPE')
