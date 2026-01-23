{
    'name': "Starry Lord HRM 薪資管理",
    'summary': "Starry Lord HRM",
    'description': "Starry Lord HRM 薪資管理",
    'author': "Starry Lord",
    'website': "https://www.starrylord.com.tw",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/19.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'HRM',
    'version': '19.0.1.1.0',

    # any module necessary for this one to work correctly
    # 2026-01-23: sl_hrm_overtime 已合併至 sl_hrm
    'depends': ['base', 'hr', 'sl_hrm'],

    # external python dependencies
    'external_dependencies': {
        'python': ['xlrd'],
    },

    # always loaded
    'data': [
        'security/sl_hrm_payroll_security.xml',
        'security/ir.model.access.csv',
        'views/hr_payroll_structure.xml',
        'views/hr_salary_rule.xml',
        'views/hr_salary_rule_category.xml',
        'views/hr_employee.xml',
        'views/starrylord_employee_payslip_setting.xml',
        'views/hr_payslip.xml',
        'views/res_config_settings.xml',
        'views/sl_bonus_record.xml',
        'views/hr_payslip_bonus.xml',
        'views/sl_payroll_adjustment.xml',
        'views/payslip_withholding_statement.xml',
        'views/payslip_withholding_statement_sheet.xml',
        'data/hr_payroll_sequence.xml',
        'data/hr_payroll_data.xml',
        'data/hr_payslip_setting_data.xml',
        'report/report_hr_payslip.xml',
        'report/sl_payroll_mail_template.xml',

        'report/payslip_sheet_report_template.xml',
        'report/payslip_bonus_sheet_report_template.xml',
        'report/payslip_withholding_statement_template.xml',

        'wizard/wizard_payslip_salary_rule_add.xml',
        'wizard/wizard_payslip_line_edit.xml',
        'wizard/hr_payslip_batch_processing.xml',

        'wizard/view_payslip_sheet_report_wizard.xml',

        'views/payslip_sheet_report.xml',
        'views/menu.xml',
    ],
    # only loaded in demonstration mode
    # 'demo': [
    #     'demo/demo.xml',
    # ],
    'installable': True,
    'auto_install': False,
    'application': True,
    'license': 'LGPL-3',
}
