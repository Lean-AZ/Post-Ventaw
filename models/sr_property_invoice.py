# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) Sitaram Solutions (<https://sitaramsolutions.in/>).
#
#    For Module Support : info@sitaramsolutions.in  or Skype : contact.hiren1188
#
##############################################################################

from odoo import models, fields, api, _

class srAccountMove(models.Model):
    _inherit = 'account.move.line'
    
    tenancy_agreement = fields.Many2one('sr.tenancy.agreement', 'Agreement')

class srAccountMove(models.Model):
    _inherit = 'account.move'

    is_property_invoice = fields.Boolean('Is Property Invoice?')
    is_ajuste_de_precio = fields.Boolean(string="Es Ajuste de precio?", default=False)
    is_property_addon = fields.Boolean('Es un producto adicional de propiedad?', default=False)
    property_id = fields.Many2one('product.product', 'Property')
    tenancy_agreement = fields.Many2one('sr.tenancy.agreement', string="Tenancy Agreement")
    is_property_commission_bill = fields.Boolean('Is Property Commission Invoice?')

    mora_pagada_custom_sr = fields.Float(
        string="Monto pagado de mora",
        compute='_compute_mora_pagada',
        store=True,
        digits='Product Price',
    )

    @api.depends('payment_state', 'invoice_line_ids')
    def _compute_mora_pagada(self):
        for move in self:
            # Only calculate for property invoices that are customer invoices
            if move.is_property_invoice and move.move_type == 'out_invoice' and move.payment_state in ('partial', 'paid'):
                # Filter lines that are "mora"
                lineas_mora = move.invoice_line_ids.filtered(
                    lambda l: l.name.lower() == 'mora'
                )
                # Sum the subtotal of those lines
                move.mora_pagada_custom_sr = sum(lineas_mora.mapped('price_subtotal'))
            else:
                move.mora_pagada_custom_sr = 0.0