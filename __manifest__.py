# -*- coding: utf-8 -*-
{
    'name': "odoo_controller",

    'summary': """
        Ejemplo de controlador para API""",

    'description': """
        API del servidor de ODOO para dar servicio más dispositivos de IRCO
    """,

    'author': "Jorge Jimenez HSCO",
    'website': "https://www.hsco.es",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/12.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '5.1.1',

    # any module necessary for this one to work correctly
    'depends': ['base'],

    # always loaded
    'data': [
        # 'security/ir.model.access.csv',
        'views/views.xml',
        'views/templates.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
}