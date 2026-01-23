# -*- coding: utf-8 -*-
{
    'name': '客戶訪談登錄作業',
    'version': '19.0.1.0.0',
    'category': 'Sales/CRM',
    'summary': '客戶訪談記錄管理',
    'description': """
客戶訪談登錄作業
================

功能說明：
- 記錄業務人員拜訪客戶的相關資訊
- 追蹤訪談內容與後續動作
- 支援附件上傳

主要欄位：
- 單據單號（自動產生）
- 登錄日期
- 業務員
- 客戶資訊
- 專案關聯
- 訪談內容
- 後續動作與對策
    """,
    'author': 'EupTop',
    'website': '',
    'license': 'LGPL-3',
    'depends': [
        'base',
        'mail',
        'hr',
        'contacts',
        'project',
    ],
    'data': [
        'security/ir.model.access.csv',
        'data/sequence_data.xml',
        'views/customer_visit_views.xml',
        'views/menu.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
}
