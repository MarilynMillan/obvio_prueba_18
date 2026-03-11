# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': 'obvio',
    'category': 'Project',
    'summary': 'Gestor de Proyecto y Equipo',
    'description': 'Gestor de Proyecto y Equipo',
    'version': '18.0',
    'author': 'Ing.Marilynmillan',
    
    'depends': ['base','maintenance','project','sale_project','account', 'analytic','documents'],
    "data": [
        "security/ir.model.access.csv",
        "views/project_project_views.xml",
        "views/partner_views.xml",
        "views/partner_bank_views.xml",
        "views/account_move_views.xml",
        "views/zone_views.xml",
        "views/zone_tienda_views.xml",
        "views/zone_ubication_views.xml",
        "views/type_project_views.xml",
        "views/type_equipment_views.xml",
        "views/equipment_maintenance_views.xml",
        "views/account_analytic_account_views.xml",
        "views/project_task_views.xml",
    ],

    'demo': [],
    'license': 'LGPL-3',
    'application': True,
    'installable': True,
    'auto_install': False
}
