{
    'name': "Starry Lord HRM 考勤",
    'summary': "Starry Lord HRM Attendance",
    'description': "Starry Lord HRM Attendance",
    'author': "Starry Lord",
    'website': "https://www.starrylord.com.tw",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/12.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'HRM',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base', 'hr','sl_hrm_personal_calendar', 'hr_attendance'],
    
    # External dependencies
    'external_dependencies': {
        'python': ['pandas', 'openpyxl'],
    },
    
    # External dependencies
    'external_dependencies': {
        'python': ['pandas', 'openpyxl'],
    },

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'data/email_template_attendance_anomaly.xml',
        'data/cron_attendance_anomaly.xml',
        'wizard/wizard_hr_attendance_check.xml',
        'views/sl_attendance_repair.xml',
        'views/sl_attendance_import_view.xml',
        'views/hr_attendance_raw_view.xml',
        'views/hr_attendance_view.xml',
        'views/menu.xml',
        'views/menu_inherit.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'sl_hr_attendance/static/src/**/*',
        ],
        'sl_hr_attendance.assets_public_attendance': [
            # Front-end libraries
            ('include', 'web._assets_helpers'),
            ('include', 'web._assets_frontend_helpers'),
            'web/static/src/scss/pre_variables.scss',
            'web/static/lib/bootstrap/scss/_variables.scss',
            ('include', 'web._assets_bootstrap_frontend'),
            ('include', 'web._assets_bootstrap_backend'),
            '/web/static/lib/odoo_ui_icons/*',
            '/web/static/lib/bootstrap/scss/_functions.scss',
            '/web/static/lib/bootstrap/scss/_mixins.scss',
            '/web/static/lib/bootstrap/scss/utilities/_api.scss',
            'web/static/src/libs/fontawesome/css/font-awesome.css',
            ('include', 'web._assets_core')]
    },
    'installable': True,
    'auto_install': False,
    'application': True,
}
