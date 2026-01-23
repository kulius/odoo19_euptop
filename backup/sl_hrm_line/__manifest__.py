# -*- coding: utf-8 -*-
{
    'name': 'LINE 打卡系統',
    'version': '17.0.1.0.0',
    'category': 'Human Resources',
    'summary': 'LINE LIFF 員工綁定與 GPS 打卡系統',
    'description': '''
        LINE LIFF 打卡系統
        ==================

        功能：
        - LINE 帳號與員工綁定
        - GPS 定位打卡（上班/下班）
        - 出勤記錄查詢

        API 端點：
        - POST /api/line/check-binding - 檢查綁定狀態
        - POST /api/line/bind - 員工綁定
        - GET /api/line/user - 取得用戶資料
        - GET /api/line/attendance/today - 今日打卡狀態
        - POST /api/line/attendance/clock - 打卡
        - GET /api/line/attendance/history - 出勤歷史
    ''',
    'author': 'SL',
    'website': '',
    'license': 'LGPL-3',
    'depends': [
        'base',
        'hr',
        'hr_attendance',
    ],
    'data': [
        'security/ir.model.access.csv',
        'views/hr_employee_views.xml',
        # 'views/hr_attendance_views.xml',  # Odoo 17 已內建 GPS 欄位視圖
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
}
