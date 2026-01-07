# -*- coding: utf-8 -*-
{
    'name': '諾內客製化',
    'version': '19.0.1.0.0',
    'category': 'Sales/Purchase',
    'summary': '擴展產品模型，新增舊產品編號和供應商編號欄位',
    'description': """
        EP Thenone 諾內客製化

    """,
    'author': 'EP Thenone',
    'website': '',
    'depends': [
        'base',
        'product',
        'sale',
        'purchase',
        'mrp',
    ],
    'data': [
        'views/product_template_views.xml',
        'views/sale_order_views.xml',
        'views/purchase_order_views.xml',
        'views/mrp_bom_views.xml',
    ],
    'installable': True,
    'auto_install': False,
    'application': False,
    'license': 'LGPL-3',
}
