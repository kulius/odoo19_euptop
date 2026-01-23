# -*- coding: utf-8 -*-

from odoo import models, api
from datetime import datetime
import pytz


class HrAttendance(models.Model):
    _inherit = 'hr.attendance'
    _description = 'Attendance with LINE Clock'

    # Odoo 19 已內建以下欄位，無需重新定義：
    # in_latitude, in_longitude, out_latitude, out_longitude
    # in_mode, out_mode, in_city, out_city 等

    @api.model
    def get_today_status(self, employee_id):
        """
        取得員工今日打卡狀態
        :param employee_id: 員工 ID
        :return: dict
        """
        tz = pytz.timezone('Asia/Taipei')
        now = datetime.now(tz)
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        today_end = now.replace(hour=23, minute=59, second=59, microsecond=999999)

        # 轉換為 UTC 查詢
        today_start_utc = today_start.astimezone(pytz.UTC).replace(tzinfo=None)
        today_end_utc = today_end.astimezone(pytz.UTC).replace(tzinfo=None)

        # 查詢今日打卡記錄
        attendance = self.search([
            ('employee_id', '=', employee_id),
            ('check_in', '>=', today_start_utc),
            ('check_in', '<=', today_end_utc)
        ], order='check_in desc', limit=1)

        if attendance:
            # 轉換時間為台北時區
            check_in_local = attendance.check_in.replace(tzinfo=pytz.UTC).astimezone(tz)
            check_out_local = None
            if attendance.check_out:
                check_out_local = attendance.check_out.replace(tzinfo=pytz.UTC).astimezone(tz)

            return {
                'success': True,
                'data': {
                    'id': attendance.id,
                    'status': 'clocked_out' if attendance.check_out else 'clocked_in',
                    'check_in': check_in_local.strftime('%Y-%m-%d %H:%M:%S'),
                    'check_in_time': check_in_local.strftime('%H:%M'),
                    'check_out': check_out_local.strftime('%Y-%m-%d %H:%M:%S') if check_out_local else None,
                    'check_out_time': check_out_local.strftime('%H:%M') if check_out_local else None,
                    'check_in_latitude': attendance.in_latitude,
                    'check_in_longitude': attendance.in_longitude,
                    'check_out_latitude': attendance.out_latitude,
                    'check_out_longitude': attendance.out_longitude,
                }
            }
        else:
            return {
                'success': True,
                'data': {
                    'status': 'not_clocked_in',
                    'check_in': None,
                    'check_out': None
                }
            }

    @api.model
    def clock_action(self, employee_id, clock_type, latitude=None, longitude=None, accuracy=None):
        """
        執行打卡動作
        :param employee_id: 員工 ID
        :param clock_type: 'in' 上班 或 'out' 下班
        :param latitude: GPS 緯度
        :param longitude: GPS 經度
        :param accuracy: GPS 精確度 (目前未使用，Odoo 19 無此欄位)
        :return: dict
        """
        tz = pytz.timezone('Asia/Taipei')
        now = datetime.now(tz)
        now_utc = now.astimezone(pytz.UTC).replace(tzinfo=None)

        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        today_start_utc = today_start.astimezone(pytz.UTC).replace(tzinfo=None)
        today_end = now.replace(hour=23, minute=59, second=59, microsecond=999999)
        today_end_utc = today_end.astimezone(pytz.UTC).replace(tzinfo=None)

        if clock_type == 'in':
            # 檢查今日是否已打過上班卡
            existing = self.search([
                ('employee_id', '=', employee_id),
                ('check_in', '>=', today_start_utc),
                ('check_in', '<=', today_end_utc)
            ], limit=1)

            if existing:
                check_in_local = existing.check_in.replace(tzinfo=pytz.UTC).astimezone(tz)
                return {
                    'success': False,
                    'error': {
                        'code': 'ALREADY_CLOCKED_IN',
                        'message': f'今日已於 {check_in_local.strftime("%H:%M")} 打過上班卡'
                    }
                }

            # 建立新的打卡記錄 (使用 Odoo 19 內建欄位名稱)
            attendance = self.create({
                'employee_id': employee_id,
                'check_in': now_utc,
                'in_latitude': latitude,
                'in_longitude': longitude,
                'in_mode': 'systray',  # 標記為系統打卡
            })

            return {
                'success': True,
                'data': {
                    'id': attendance.id,
                    'type': 'in',
                    'status': 'clocked_in',
                    'time': now.strftime('%H:%M'),
                    'datetime': now.strftime('%Y-%m-%d %H:%M:%S'),
                    'latitude': latitude,
                    'longitude': longitude,
                }
            }

        elif clock_type == 'out':
            # 查找今日上班記錄
            attendance = self.search([
                ('employee_id', '=', employee_id),
                ('check_in', '>=', today_start_utc),
                ('check_in', '<=', today_end_utc),
                ('check_out', '=', False)
            ], order='check_in desc', limit=1)

            if not attendance:
                return {
                    'success': False,
                    'error': {
                        'code': 'NOT_CLOCKED_IN',
                        'message': '今日尚未打上班卡，無法打下班卡'
                    }
                }

            # 更新下班時間 (使用 Odoo 19 內建欄位名稱)
            attendance.write({
                'check_out': now_utc,
                'out_latitude': latitude,
                'out_longitude': longitude,
                'out_mode': 'systray',
            })

            return {
                'success': True,
                'data': {
                    'id': attendance.id,
                    'type': 'out',
                    'status': 'clocked_out',
                    'time': now.strftime('%H:%M'),
                    'datetime': now.strftime('%Y-%m-%d %H:%M:%S'),
                    'latitude': latitude,
                    'longitude': longitude,
                }
            }

        else:
            return {
                'success': False,
                'error': {
                    'code': 'INVALID_TYPE',
                    'message': '無效的打卡類型'
                }
            }

    @api.model
    def get_attendance_history(self, employee_id, limit=30, offset=0):
        """
        取得出勤歷史記錄
        :param employee_id: 員工 ID
        :param limit: 筆數限制
        :param offset: 偏移量
        :return: dict
        """
        tz = pytz.timezone('Asia/Taipei')

        attendances = self.search([
            ('employee_id', '=', employee_id)
        ], order='check_in desc', limit=limit, offset=offset)

        records = []
        for att in attendances:
            check_in_local = att.check_in.replace(tzinfo=pytz.UTC).astimezone(tz)
            check_out_local = None
            if att.check_out:
                check_out_local = att.check_out.replace(tzinfo=pytz.UTC).astimezone(tz)

            # 計算工時
            worked_hours = None
            if att.check_out and att.check_in:
                delta = att.check_out - att.check_in
                worked_hours = round(delta.total_seconds() / 3600, 2)

            records.append({
                'id': att.id,
                'date': check_in_local.strftime('%Y-%m-%d'),
                'weekday': ['一', '二', '三', '四', '五', '六', '日'][check_in_local.weekday()],
                'check_in': check_in_local.strftime('%H:%M'),
                'check_out': check_out_local.strftime('%H:%M') if check_out_local else None,
                'worked_hours': worked_hours,
                'check_in_latitude': att.in_latitude,
                'check_in_longitude': att.in_longitude,
                'check_out_latitude': att.out_latitude,
                'check_out_longitude': att.out_longitude,
            })

        return {
            'success': True,
            'data': {
                'records': records,
                'total': self.search_count([('employee_id', '=', employee_id)])
            }
        }
