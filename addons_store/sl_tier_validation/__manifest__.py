{
    'name': "Starry Lord Base Tier Validation",
    'summary': "Starry Lord Base Tier Validation",
    'description': "Starry Lord Base Tier Validation",
    'author': "Starry Lord",
    'website': "https://www.starrylord.com.tw",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/19.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Tools',
    'version': '19.0.1.0.0',

    # any module necessary for this one to work correctly
    'depends': ['base', 'base_tier_validation'],
    'data': [
        'security/sl_tier_review_security.xml',
        'security/ir.model.access.csv',
        'views/tier_portal_todo.xml',
        'views/tier_portal_form.xml',
        'views/menu.xml',
        "templates/tier_validation_templates.xml",
    ],
    # TODO: OWL 元件需要升級到 Odoo 19 OWL 3
    # "assets": {
    #     "web.assets_backend": [
    #         "/sl_tier_validation/static/src/components/tier_review_log_widget/tier_review_log_widget.esm.js",
    #         "/sl_tier_validation/static/src/components/tier_review_log_widget/tier_review_log_widget.scss",
    #         "/sl_tier_validation/static/src/components/tier_review_log_widget/tier_review_log_widget.xml",
    #     ],
    # },
    'installable': True,
    'auto_install': False,
    'application': False,
    'license': 'LGPL-3',
}
