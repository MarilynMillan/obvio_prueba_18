# -*- coding: utf-8 -*-
{
    'name': "Sale Order Customization",
    'summary': "",
    'description': """
    Customizations in Sale Order
    """,
    'author': "Navegasoft S.A.S",
    'website': "https://www.navegasoft.com/",
    'category': 'Sales/Sales',
    'version': '18.0.1.0.0',
    'depends': ['project', 'sale', 'sale_management', 'portal', 'obvio'],
    'data': [
        'security/ir.model.access.csv',
        'data/sequence.xml',
        "data/cron.xml",
        'reports/sale_order_report.xml',
        'views/sale_order_views.xml',
        'views/brand_views.xml',
        'views/sale_portal_report_preview.xml',
    ],

    "assets": {
        "web.assets_backend": [
                "sale_order_customization/static/src/js/*",
            ],
        "web.reports_assets_common": [
            "sale_order_customization/static/src/scss/sale_order_report.scss",
        ],
        # Fallback
        "web.report_assets_common": [
            "sale_order_customization/static/src/scss/sale_order_report.scss",
        ],
    },

    'installable': True,
    'application': False,
    'license': 'LGPL-3',
}

