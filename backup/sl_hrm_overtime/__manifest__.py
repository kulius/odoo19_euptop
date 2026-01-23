{
    'name': "Starry Lord HRM 加班",
    'summary': "Starry Lord HRM",
    'description': "Starry Lord HRM 加班",
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
        'security/starrylord_overtime_security.xml',
        'security/ir.model.access.csv',
        'security/sl_hrm_overtime_security.xml',
        'views/starrylord_overtime_apply.xml',
        'views/starrylord_overtime_settings.xml',
        'views/starrylord_overtime_type.xml',
        'views/starrylord_holiday_allocation_view.xml',
        # 'views/starrylord_holiday_min_list.xml',
        # 'views/starrylord_holiday_allocation.xml',
        # 'views/starrylord_holiday_personal.xml',
        # 'views/hr_public_holiday.xml',
        'wizard/overtime_apply_record_wizard_form.xml',
        'data/starrylord_overtime_data.xml',
        'views/overtime_exchange_consent_views.xml',
        'report/overtime_exchange_consent_templates.xml',
        'views/menu.xml',
    ],
    # only loaded in demonstration mode
    # 'demo': [
    #     'demo/demo.xml',
    # ],
    'installable': True,
    'auto_install': False,
    'application': True,
}