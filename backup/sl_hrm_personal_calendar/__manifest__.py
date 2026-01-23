{
    'name': "Starry Lord 個人行事曆",
    'summary': "Starry Lord HRM",
    'description': "Starry Lord HRM 個人行事曆",
    'author': "Starry Lord",
    'website': "https://www.starrylord.com.tw",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/12.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'HRM',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base','hr'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'views/hr_schedule.xml',
        'views/hr_schedule_time_type.xml',
        'views/hr_personal_calendar.xml',
        'views/hr_employee.xml',
        # 'views/starrylord_holiday_allocation.xml',
        # 'views/starrylord_holiday_personal.xml',
        # 'views/hr_public_holiday.xml',
        # 'wizard/wizard_holiday_batch_allocation.xml',

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