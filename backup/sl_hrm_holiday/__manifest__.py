{
    'name': "Starry Lord HRM 請休假",
    'summary': "Starry Lord HRM",
    'description': "Starry Lord HRM 請休假",
    'author': "Starry Lord",
    'website': "https://www.starrylord.com.tw",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/12.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'HRM',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base', 'hr', 'sl_tier_validation', 'sl_hr_attendance'],

    # always loaded
    'data': [
        'security/starrylord_holiday_security.xml',
        'security/ir.model.access.csv',
        'security/sl_hrm_holiday_security.xml',
        'data/starrylord_holiday_apply_data.xml',
        'data/holiday_cron.xml',
        'data/starrylord_holiday_apply_setting_data.xml',
        'views/starrylord_holiday_apply.xml',
        'views/starrylord_holiday_settings.xml',
        'views/starrylord_holiday_type.xml',
        'views/starrylord_holiday_hour_list.xml',
        'views/starrylord_holiday_min_list.xml',
        'views/starrylord_holiday_allocation.xml',
        'views/starrylord_holiday_personal.xml',
        'views/starrylord_holiday_used_record.xml',
        'views/hr_public_holiday.xml',
        'views/starrylord_holiday_cancel.xml',
        'views/starrylord_annual_leave_setting.xml',
        'wizard/wizard_holiday_batch_allocation.xml',
        'wizard/holiday_used_record_wizard_form.xml',
        'views/menu.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'sl_hrm_holiday/static/src/views/*.js',
            'sl_hrm_holiday/static/src/**/*.xml',
        ],
    },
    'installable': True,
    'auto_install': False,
    'application': True,
}