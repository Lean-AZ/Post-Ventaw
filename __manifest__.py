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
    'depends': ['base', 'account', 'utm','product', 'civiltec_contact_fields', 'crm', 'sr_manual_currency_exchange_rate', 'helpdesk', 'project', 'mail', 'website'],
    'data': [
        'security/property_security.xml',
        'security/ir.model.access.csv',
        'data/ir_sequence_data.xml',
        'data/ir_cron_data.xml',
        'data/ir_sequence_data.xml',     
        'data/helpdesk_stage_data.xml',
        'data/helpdesk_ticket_category_data.xml',
        'data/mail_template_data.xml',
        'data/cron.xml',
        'views/sr_tenant_agreement.xml',
        'views/sr_property_product_view.xml',
        'views/sr_property_landlord_agent.xml',
        'views/sr_agent_commission.xml',
        'views/sr_property_project.xml',
        'views/sr_property_management_view.xml',
        'views/sr_property_invoice.xml',
        'views/sr_property_management_configuration_view.xml',
        'views/sr_property_lead.xml',
        'views/wizzards/sr_agent_comission_wizzard.xml',
        'reports/reporte_separacion_action.xml',
        'reports/reporte_separacion_template.xml',
        'reports/recibo_pago_template.xml',
        'reports/recibo_pago_unidad_action.xml',
        'reports/contrato_action.xml',
        'reports/contrato_template.xml',
        'reports/ladano_contrato_action.xml',
        'reports/ladano_contrato_template.xml',
        'reports/contrato_oceance_action.xml',
        'reports/contrato_oceance_template.xml',
        'reports/contrato_ocean_v_action.xml',
        'reports/contrato_ocean_v_template.xml',
        'reports/entrega_action.xml',
        'reports/entrega_template.xml',
        'reports/report_invoice_lines_grouped_action.xml',
        'reports/report_invoice_lines_grouped.xml',
        'reports/retenciones_action.xml',
        'reports/retenciones_template.xml',
        'reports/payment_action.xml',
        'reports/payment_template.xml',
        'reports/retenciones_itbis_action.xml',
        'reports/retenciones_itbis_template.xml',
        'reports/retenciones_mixtas_action.xml',
        'reports/retenciones_mixtas_template.xml',
        'reports/retenciones_30_itbis_action.xml',
        'reports/retenciones_itbis_30_template.xml',
        'views/helpdesk_ticket_views.xml',
        'views/warranty_portal_templates.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'sr_property_rental_management/static/css/report_styles.css',
        ],
    },
    'installable': True,
    'auto_install': False,
    'application': True,
    'live_test_url':'https://youtu.be/MTWHjYuEJng',
    "images":['static/description/banner.png'],
    "post_init_hook": "post_init_hook",
}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
