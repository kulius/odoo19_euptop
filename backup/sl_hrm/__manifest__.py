{
    'name': "Starry Lord HRM 人資管理",
    'summary': "Starry Lord HRM",
    'description': "Starry Lord HRM",
    'author': "Starry Lord",
    'website': "https://www.starrylord.com.tw",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/12.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'HRM',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base', 'hr', 'hr_skills'],

    # always loaded
    'data': [
        'data/sl_employee_sequence.xml',
        'security/ir.model.access.csv',
        'security/sl_hrm_security.xml',
        'wizard/wizard_dependents_add.xml',
        'wizard/wizard_labor_insurance_change.xml',
        'wizard/wizard_health_insurance_change.xml',
        'wizard/wizard_labor_pension_change.xml',
        'wizard/wizard_labor_harm_insurance_change.xml',
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