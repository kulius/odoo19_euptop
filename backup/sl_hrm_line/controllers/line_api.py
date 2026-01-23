# -*- coding: utf-8 -*-

import json
import logging
from odoo import http, fields
from odoo.http import request, Response

_logger = logging.getLogger(__name__)

# CORS Headers
CORS_HEADERS = {
    'Access-Control-Allow-Origin': '*',
    'Access-Control-Allow-Methods': 'GET, POST, PUT, DELETE, OPTIONS',
    'Access-Control-Allow-Headers': 'Content-Type, Authorization, X-Line-User-Id, Origin, Accept',
    'Access-Control-Max-Age': '86400',
}


class SLLineAPI(http.Controller):
    """LINE 打卡系統 REST API"""

    def _cors_response(self):
        """處理 OPTIONS 預檢請求"""
        return Response(
            status=204,
            headers=CORS_HEADERS
        )

    def _json_response(self, data, status=200):
        """統一 JSON 回應格式"""
        return Response(
            json.dumps(data, ensure_ascii=False),
            status=status,
            mimetype='application/json',
            headers=CORS_HEADERS
        )

    def _error_response(self, code, message, status=400):
        """統一錯誤回應格式"""
        return self._json_response({
            'success': False,
            'error': {
                'code': code,
                'message': message
            }
        }, status=status)

    def _get_line_user_id(self):
        """從請求中取得 LINE User ID"""
        return (
            request.httprequest.headers.get('X-Line-User-Id') or
            request.params.get('line_user_id')
        )

    def _get_employee_by_line_id(self, line_user_id):
        """透過 LINE User ID 取得員工"""
        if not line_user_id:
            return None
        employee = request.env['hr.employee'].sudo().search([
            ('line_user_id', '=', line_user_id)
        ], limit=1)
        return employee if employee else None

    # ==================== 用戶綁定 API ====================

    @http.route('/api/line/check-binding', type='http', auth='public', methods=['POST', 'OPTIONS'], csrf=False)
    def check_binding(self, **kwargs):
        """
        檢查用戶是否已綁定
        POST /api/line/check-binding
        Body: {userId, displayName, pictureUrl}
        """
        if request.httprequest.method == 'OPTIONS':
            return self._cors_response()

        try:
            data = json.loads(request.httprequest.data.decode('utf-8'))
        except (json.JSONDecodeError, UnicodeDecodeError):
            return self._error_response('INVALID_JSON', '無效的 JSON 格式')

        line_user_id = data.get('userId')
        if not line_user_id:
            return self._error_response('MISSING_USER_ID', '缺少 LINE User ID')

        try:
            employee = self._get_employee_by_line_id(line_user_id)

            if employee:
                # 已綁定，更新 LINE 資料
                employee.write({
                    'line_display_name': data.get('displayName'),
                    'line_picture_url': data.get('pictureUrl'),
                })
                return self._json_response({
                    'success': True,
                    'isBound': True,
                    'data': employee._get_employee_data()
                })
            else:
                # 未綁定
                return self._json_response({
                    'success': True,
                    'isBound': False,
                    'data': None
                })
        except Exception as e:
            _logger.exception('Check binding error')
            return self._error_response('SERVER_ERROR', str(e), status=500)

    @http.route('/api/line/bind', type='http', auth='public', methods=['POST', 'OPTIONS'], csrf=False)
    def bind_employee(self, **kwargs):
        """
        員工綁定（用姓名綁定 LINE 帳號）
        POST /api/line/bind
        Body: {line_user_id, line_display_name, line_picture_url, employee_name}
        """
        if request.httprequest.method == 'OPTIONS':
            return self._cors_response()

        try:
            data = json.loads(request.httprequest.data.decode('utf-8'))
        except (json.JSONDecodeError, UnicodeDecodeError):
            return self._error_response('INVALID_JSON', '無效的 JSON 格式')

        line_user_id = data.get('line_user_id')
        line_display_name = data.get('line_display_name')
        line_picture_url = data.get('line_picture_url')
        employee_name = data.get('employee_name')

        if not line_user_id:
            return self._error_response('MISSING_USER_ID', '缺少 LINE User ID')
        if not employee_name:
            return self._error_response('MISSING_NAME', '缺少員工姓名')

        try:
            Employee = request.env['hr.employee'].sudo()

            # 檢查 LINE 帳號是否已綁定
            existing = self._get_employee_by_line_id(line_user_id)
            if existing:
                return self._error_response('ALREADY_BOUND', '此 LINE 帳號已綁定其他員工')

            # 用姓名查找員工（未綁定的）
            employee = Employee.search([
                ('name', '=', employee_name),
                ('line_user_id', '=', False)
            ], limit=1)

            if not employee:
                # 檢查是否已被其他 LINE 帳號綁定
                bound_employee = Employee.search([
                    ('name', '=', employee_name),
                    ('line_user_id', '!=', False)
                ], limit=1)

                if bound_employee:
                    return self._error_response('EMPLOYEE_BOUND', '此員工已綁定其他 LINE 帳號')

                # 找不到員工
                return self._json_response({
                    'success': True,
                    'data': {'matched': False}
                })

            # 綁定成功
            employee.write({
                'line_user_id': line_user_id,
                'line_display_name': line_display_name,
                'line_picture_url': line_picture_url,
                'line_binding_date': fields.Datetime.now(),
            })

            return self._json_response({
                'success': True,
                'data': {
                    'matched': True,
                    **employee._get_employee_data()
                }
            })
        except Exception as e:
            _logger.exception('Bind employee error')
            return self._error_response('BIND_ERROR', str(e), status=500)

    @http.route('/api/line/user', type='http', auth='public', methods=['GET', 'OPTIONS'], csrf=False)
    def get_user(self, **kwargs):
        """
        取得用戶資料
        GET /api/line/user
        Header: X-Line-User-Id
        """
        if request.httprequest.method == 'OPTIONS':
            return self._cors_response()

        line_user_id = self._get_line_user_id()
        if not line_user_id:
            return self._error_response('MISSING_USER_ID', '缺少 LINE User ID', status=401)

        employee = self._get_employee_by_line_id(line_user_id)
        if not employee:
            return self._error_response('USER_NOT_FOUND', '用戶尚未綁定', status=404)

        return self._json_response({
            'success': True,
            'data': employee._get_employee_data()
        })

    # ==================== 打卡 API ====================
    # 注意：需要安裝 hr_attendance 模組才能使用打卡功能

    def _check_attendance_module(self):
        """檢查 hr_attendance 模組是否已安裝"""
        return 'hr.attendance' in request.env

    @http.route('/api/line/attendance/today', type='http', auth='public', methods=['GET', 'OPTIONS'], csrf=False)
    def get_today_attendance(self, **kwargs):
        """
        取得今日打卡狀態
        GET /api/line/attendance/today
        Header: X-Line-User-Id
        """
        if request.httprequest.method == 'OPTIONS':
            return self._cors_response()

        if not self._check_attendance_module():
            return self._error_response('MODULE_NOT_INSTALLED', '打卡功能尚未啟用，請先安裝 hr_attendance 模組', status=503)

        line_user_id = self._get_line_user_id()
        if not line_user_id:
            return self._error_response('MISSING_USER_ID', '缺少 LINE User ID', status=401)

        employee = self._get_employee_by_line_id(line_user_id)
        if not employee:
            return self._error_response('USER_NOT_FOUND', '用戶尚未綁定', status=404)

        try:
            Attendance = request.env['hr.attendance'].sudo()
            result = Attendance.get_today_status(employee.id)
            return self._json_response(result)
        except Exception as e:
            _logger.exception('Get today attendance error')
            return self._error_response('SERVER_ERROR', str(e), status=500)

    @http.route('/api/line/attendance/clock', type='http', auth='public', methods=['POST', 'OPTIONS'], csrf=False)
    def clock_in_out(self, **kwargs):
        """
        打卡（上班/下班）
        POST /api/line/attendance/clock
        Header: X-Line-User-Id
        Body: {type: 'in'|'out', latitude, longitude, accuracy}
        """
        if request.httprequest.method == 'OPTIONS':
            return self._cors_response()

        if not self._check_attendance_module():
            return self._error_response('MODULE_NOT_INSTALLED', '打卡功能尚未啟用，請先安裝 hr_attendance 模組', status=503)

        line_user_id = self._get_line_user_id()
        if not line_user_id:
            return self._error_response('MISSING_USER_ID', '缺少 LINE User ID', status=401)

        employee = self._get_employee_by_line_id(line_user_id)
        if not employee:
            return self._error_response('USER_NOT_FOUND', '用戶尚未綁定', status=404)

        try:
            data = json.loads(request.httprequest.data.decode('utf-8'))
        except (json.JSONDecodeError, UnicodeDecodeError):
            return self._error_response('INVALID_JSON', '無效的 JSON 格式')

        clock_type = data.get('type')
        latitude = data.get('latitude')
        longitude = data.get('longitude')
        accuracy = data.get('accuracy')

        if clock_type not in ('in', 'out'):
            return self._error_response('INVALID_TYPE', '打卡類型必須為 in 或 out')

        try:
            Attendance = request.env['hr.attendance'].sudo()
            result = Attendance.clock_action(
                employee_id=employee.id,
                clock_type=clock_type,
                latitude=latitude,
                longitude=longitude,
                accuracy=accuracy
            )
            return self._json_response(result)
        except Exception as e:
            _logger.exception('Clock in/out error')
            return self._error_response('SERVER_ERROR', str(e), status=500)

    @http.route('/api/line/attendance/history', type='http', auth='public', methods=['GET', 'OPTIONS'], csrf=False)
    def get_attendance_history(self, **kwargs):
        """
        取得出勤歷史
        GET /api/line/attendance/history?limit=30&offset=0
        Header: X-Line-User-Id
        """
        if request.httprequest.method == 'OPTIONS':
            return self._cors_response()

        if not self._check_attendance_module():
            return self._error_response('MODULE_NOT_INSTALLED', '打卡功能尚未啟用，請先安裝 hr_attendance 模組', status=503)

        line_user_id = self._get_line_user_id()
        if not line_user_id:
            return self._error_response('MISSING_USER_ID', '缺少 LINE User ID', status=401)

        employee = self._get_employee_by_line_id(line_user_id)
        if not employee:
            return self._error_response('USER_NOT_FOUND', '用戶尚未綁定', status=404)

        try:
            limit = int(kwargs.get('limit', 30))
            offset = int(kwargs.get('offset', 0))
        except ValueError:
            limit = 30
            offset = 0

        try:
            Attendance = request.env['hr.attendance'].sudo()
            result = Attendance.get_attendance_history(
                employee_id=employee.id,
                limit=limit,
                offset=offset
            )
            return self._json_response(result)
        except Exception as e:
            _logger.exception('Get attendance history error')
            return self._error_response('SERVER_ERROR', str(e), status=500)
