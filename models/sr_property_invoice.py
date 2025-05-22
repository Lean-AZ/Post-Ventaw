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
                # Get all payments related to this invoice

                # Get reconciled payment information
                payments_info = move._get_reconciled_info_JSON_values()
                mora_paid_temp = 0.0
                # Search each payment record and sum mora_pagada_custom_sr
                for payment_info in payments_info:
                    payment_id = payment_info.get('account_payment_id')
                    if payment_id:
                        payment = move.env['account.payment'].browse(payment_id)
                        mora_paid_temp += payment.mora_pagada_custom_sr
                # Initialize total mora paid from all payments
                if mora_paid_temp > move.computed_mora:
                    move.mora_pagada_custom_sr = move.computed_mora
                else:
                    move.mora_pagada_custom_sr = mora_paid_temp
                move.capital_pagado_custom_sr = amount_paid_temp - move.mora_pagada_custom_sr
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

    def action_register_payment(self):
        # Handle multiple records case
        if len(self) > 1:
            # If multiple records, only process the first one
            all_records = self
            total_mora_pendiente = 0.0
            total_capital_pendiente = 0.0
            action = super(srAccountMove, all_records).action_register_payment()
            for record in all_records:
                if record.is_property_invoice:
                    mora_pendiente = record.computed_mora - record.mora_pagada_custom_sr
                    total_mora_pendiente += mora_pendiente
                    total_capital_pendiente += record.amount_residual
                action['context'].update({
                    'default_mora_pagada_custom_sr': total_mora_pendiente if total_mora_pendiente > 0 else 0.0,
                    'default_is_property_invoice': all_records[0].is_property_invoice,
                    'default_group_payment': True,
                    'default_capital_pagado_custom_sr': total_capital_pendiente - total_mora_pendiente if total_capital_pendiente - total_mora_pendiente > 0 else 0.0,
                })
        else:
            # Single record case
            action = super().action_register_payment()
            if self.is_property_invoice:
                mora_pendiente = self.computed_mora - self.mora_pagada_custom_sr
                capital_pendiente = self.amount_residual - self.mora_pagada_custom_sr
                action['context'].update({
                    'default_mora_pagada_custom_sr': mora_pendiente if mora_pendiente > 0 else 0.0,
                    'default_is_property_invoice': self.is_property_invoice,
                    'default_capital_pagado_custom_sr': capital_pendiente if capital_pendiente > 0 else 0.0,
                })

        def _create_payments(self):
            payments = super().action_create_payments()
            for payment in payments:
                payment.mora_pagada_custom_sr = self.mora_pagada_custom_sr
            return payments

        return action


class srAccountPaymentWizard(models.TransientModel):
    _inherit = 'account.payment.register'

    is_property_invoice = fields.Boolean('Is Property Invoice?')
    capital_pagado_custom_sr = fields.Float(
        string="Monto pagado de capital",
        store=True,
        digits='Product Price',
        default=0.00,
        compute='_compute_capital_pagado',
    )
    mora_pagada_custom_sr = fields.Float(
        string="Monto pagado de mora",
        store=True,
        digits='Product Price',
        default=0.00,
    )

    @api.depends('is_property_invoice', 'amount', 'mora_pagada_custom_sr')
    def _compute_capital_pagado(self):
        for wizard in self:
            if wizard.is_property_invoice:
                wizard.capital_pagado_custom_sr = wizard.amount - wizard.mora_pagada_custom_sr
            else:
                wizard.capital_pagado_custom_sr = 0.00

class srAccountPayment(models.Model):
    _inherit = 'account.payment'
    is_property_invoice = fields.Boolean('Is Property Invoice?')

    capital_pagado_custom_sr = fields.Float(
        string="Monto pagado de capital",
        store=True,
        digits='Product Price',
        default=0.0,
    )

    mora_pagada_custom_sr = fields.Float(
        string="Monto pagado de mora",
        store=True,
        digits='Product Price',
        default=0.0,
        tracking=True,
    )
    