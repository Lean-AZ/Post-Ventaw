# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) Sitaram Solutions (<https://sitaramsolutions.in/>).
#
#    For Module Support : info@sitaramsolutions.in  or Skype : contact.hiren1188
#
##############################################################################

{
    'name': 'Venta y Gestión de Propiedades',
    'version': '17.0.0.0',
    'category': 'Extra Addons',
    "license": "OPL-1",
    'summary': 'Gestión de Venta y Alquiler de Propiedades',
    'description': """
        odoo Real Estate Management
""",
    "price": 50,
    "currency": 'EUR',
    'author': 'RhodeTech',
    'website':"https://www.rhodetec.co",
    'depends': ['base', 'account', 'utm','product', 'civiltec_contact_fields', 'crm'],
    'data': [
        'security/property_security.xml',
        'security/ir.model.access.csv',
        'data/ir_sequence_data.xml',
        'data/ir_cron_data.xml',
        'data/cron.xml',
        'views/sr_property_invoice.xml',
        'views/sr_agent_commission.xml',
        'views/sr_tenant_agreement.xml',
        'views/sr_property_landlord_agent.xml',
        'views/sr_property_product_view.xml',
        'views/sr_property_management_view.xml',
        'views/sr_property_management_configuration_view.xml',
    ],
    'installable': True,
    'auto_install': False,
    'application': True,
    'live_test_url':'https://youtu.be/MTWHjYuEJng',
    "images":['static/description/banner.png'],
    "post_init_hook": "post_init_hook",
}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
