{
    'name': "Starry Lord HRM 人資管理",
    'summary': "整合人資管理、請假、加班、考勤功能",
    'description': """
    Starry Lord HRM 整合模組
    ========================
    整合以下功能：
    - 人資基本資料管理
    - 勞健保、勞退管理
    - 個人行事曆與排班
    - 請假申請與管理
    - 加班申請與管理
    - 考勤打卡與管理
    """,
    'author': "Starry Lord",
    'website': "https://www.starrylord.com.tw",
    'category': 'HRM',
    'version': '19.0.2.0.0',

    # 合併後的依賴
    'depends': [
        'base',
        'hr',
        'hr_skills',
        'hr_attendance',
        'base_tier_validation',
        'sl_tier_validation',
    ],

    # 外部 Python 依賴 (從 sl_hr_attendance)
    'external_dependencies': {
        'python': ['pandas', 'openpyxl'],
    },

    'data': [
        # ========== Security ==========
        'security/ir.model.access.csv',
        'security/sl_hrm_security.xml',

        # ========== Data ==========
        'data/sl_employee_sequence.xml',
        'data/starrylord_holiday_apply_data.xml',
        'data/starrylord_holiday_apply_setting_data.xml',
        'data/starrylord_overtime_data.xml',
        'data/email_template_attendance_anomaly.xml',
        # 'data/holiday_cron.xml',  # TODO: 需要修正

        # ========== Wizard ==========
        'wizard/wizard_dependents_add.xml',
        'wizard/wizard_labor_insurance_change.xml',
        'wizard/wizard_health_insurance_change.xml',
        'wizard/wizard_labor_pension_change.xml',
        'wizard/wizard_labor_harm_insurance_change.xml',
        'wizard/wizard_holiday_batch_allocation.xml',
        'wizard/holiday_used_record_wizard_form.xml',
        'wizard/overtime_apply_record_wizard_form.xml',
        'wizard/wizard_hr_attendance_check.xml',

        # ========== Views - 核心人資 ==========
        'views/hr_employee.xml',
        'views/hr_setting.xml',
        'views/hr_employee_public.xml',
        'views/hr_labor_insurance_gap.xml',
        'views/hr_labor_harm_insurance_gap.xml',
        'views/hr_salary_tax_gap.xml',
        'views/hr_health_insurance_gap.xml',
        'views/hr_batch_operation_views.xml',
        'views/hr_labor_pension_gap.xml',
        'views/hr_department.xml',
        'views/res_users.xml',
        'views/res_company.xml',
        'views/hr_work_location.xml',
        'views/sl_res_partner.xml',
        'views/sl_plant_area.xml',
        'views/sl_hr_health_report_check_setting.xml',
        'views/sl_hr_license_check_setting.xml',

        # ========== Views - 個人行事曆 (從 sl_hrm_personal_calendar) ==========
        'views/starrylord_time_list.xml',
        'views/hr_schedule.xml',
        'views/hr_schedule_time_type.xml',
        'views/hr_personal_calendar.xml',

        # ========== Views - 考勤 (從 sl_hr_attendance) - 必須在加班之前載入 ==========
        'views/sl_attendance_repair.xml',
        'views/sl_attendance_import_view.xml',
        'views/hr_attendance_raw_view.xml',
        'views/hr_attendance_view.xml',
        'views/menu_inherit.xml',

        # ========== Views - 請假 (從 sl_hrm_holiday) ==========
        'views/starrylord_holiday_apply.xml',
        'views/starrylord_holiday_settings.xml',
        'views/starrylord_holiday_type.xml',
        'views/starrylord_holiday_hour_list.xml',
        'views/starrylord_holiday_min_list.xml',
        'views/starrylord_holiday_allocation.xml',
        'views/starrylord_holiday_personal.xml',
        'views/starrylord_holiday_used_record.xml',
        'views/starrylord_holiday_cancel.xml',
        'views/hr_public_holiday.xml',
        'views/starrylord_annual_leave_setting.xml',

        # ========== Views - 加班 (從 sl_hrm_overtime) - 依賴考勤視圖 ==========
        'views/starrylord_overtime_apply.xml',
        'views/starrylord_overtime_settings.xml',
        'views/starrylord_overtime_type.xml',
        'views/starrylord_holiday_allocation_view.xml',
        'views/overtime_exchange_consent_views.xml',

        # ========== Report ==========
        'report/overtime_exchange_consent_templates.xml',

        # ========== Menu (最後載入) ==========
        'views/starrylord_holiday_menu.xml',
        'views/starrylord_overtime_menu.xml',
        'views/menu.xml',
    ],

    'assets': {
        'web.assets_backend': [
            'sl_hrm/static/src/views/*.js',
            'sl_hrm/static/src/views/*.xml',
        ],
    },

    'installable': True,
    'auto_install': False,
    'application': True,
    'license': 'LGPL-3',
}
