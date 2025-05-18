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

    computed_mora = fields.Float(
        string="Total Mora Generada", compute="_compute_computed_mora", store=True
    )

    mora_pagada_custom_sr = fields.Float(
        string="Monto pagado de mora",
        compute='_compute_mora_pagada',
        store=True,
        digits='Product Price',
    )

    capital_pagado_custom_sr = fields.Float(
        string="Monto pagado de capital",
        compute='_compute_mora_pagada',
        store=True,
        digits='Product Price',
    )

    @api.depends('payment_state', 'invoice_line_ids', 'amount_residual')
    def _compute_mora_pagada(self):
        for move in self:
            # Only calculate for property invoices that are customer invoices
            if move.is_property_invoice and move.move_type == 'out_invoice' and move.payment_state in ('partial', 'paid'):
                # Filter lines that are "mora"
                amount_paid_temp = move.amount_total - move.amount_residual
                lineas_mora = move.invoice_line_ids.filtered(
                    lambda l: l.name.lower() == 'mora'
                )
                # Sum the subtotal of those lines
                if lineas_mora:
                    total_mora = sum(lineas_mora.mapped('price_subtotal'))
                    if amount_paid_temp >= total_mora:
                        move.mora_pagada_custom_sr = total_mora
                        move.capital_pagado_custom_sr = amount_paid_temp - total_mora
                    else:
                        move.mora_pagada_custom_sr = amount_paid_temp
                        move.capital_pagado_custom_sr = 0.0
                else:
                    move.mora_pagada_custom_sr = 0.0
                    move.capital_pagado_custom_sr = amount_paid_temp
            else:
                move.mora_pagada_custom_sr = 0.0
                move.capital_pagado_custom_sr = 0.0

    @api.depends('invoice_line_ids', 'payment_state', 'amount_residual')
    def _compute_computed_mora(self):
        for move in self:
            if move.is_property_invoice and move.move_type == 'out_invoice':
                mora_lines = move.invoice_line_ids.filtered(
                    lambda l: l.name and "mora" in l.name.lower()
                )
                move.computed_mora = sum(mora_lines.mapped('price_subtotal'))
            else:
                move.computed_mora = 0.0