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
    'name': 'Property Sale, and Rental Management',
    'version': '15.0.0.0',
    'category': 'Extra Addons',
    "license": "OPL-1",
    'summary': 'Odoo Real Estate Management, Property Sale Management, Property Rent Management, Property Lease Management, Agent Management, Tenant Management, Landlord Management, Tenancy Agreement Management, Commission Management, property contract management',
    'description': """
        odoo Real Estate Management
        odoo property Management
        Odoo property Rent Management
        Odoo Property Sale Management
        Odoo Property Lease management
        Manage Agent for property
        Manage Tenant for property
        Manage Landlord for property
        Tenancy agreement for property rent and sale
        odoo tenancy agreement management
        property tenancy agreement 
        commission management
        property commission management
        odoo commission management
        manage commission for property
        commission settlement to agent
        agent commission settlement
        property commission management
        sell property
        rent property
        create property
        Real Estate property management in odoo
        auto create invoice based on tenancy agreement date
        partial payment
        partial payment for buy property
        quick buy property
        quick sell property
        quick rent property
        manage real estate property
        property listing
        property amenities
        property invoices
        commission vendor bills
        manage property agents
        manage property owners
        manage property landlords
        manage property buyers
        manage property sellers
        manage property tenants
        calculate property commission for agent
        calculate agent commission for property
        post property listing
        easy buy property
        easy rent property
        partial payment allow for payment
        real estate property management flow
        real estate property  complete work flow
""",
    "price": 50,
    "currency": 'EUR',
    'author': 'Sitaram',
    'website':"https://www.sitaramsolutions.in",
    'depends': ['base', 'account', 'utm','product'],
    'data': [
        'security/property_security.xml',
        'security/ir.model.access.csv',
        'data/ir_sequence_data.xml',
        'data/ir_cron_data.xml',
        'views/sr_property_invoice.xml',
        'views/sr_agent_commission.xml',
        'views/sr_tenant_agreement.xml',
        'views/sr_property_landlord_agent.xml',
        'views/sr_property_product_view.xml',
        'views/sr_property_management_view.xml',
        'views/sr_property_management_configuration_view.xml',
        'views/unit.xml',

    ],
    # 'installable': True,
    # 'auto_install': False,
    # 'application': True,
    'live_test_url':'https://youtu.be/MTWHjYuEJng',
    "images":['static/description/banner.png'],
}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
