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
        # 1) Lógica previa a abrir el wizard (opcional)
        for inv in self:
            # por ejemplo, marcar un log o disparar validaciones
            _logger = inv.env['ir.logging']
            _logger.create({
                'name': 'Registro Mora',
                'type': 'server',
                'dbname': inv.env.cr.dbname,
                'message': _('Se va a registrar pago en factura %s') % inv.name,
                'level': 'INFO',
                'path': 'sr_property_rental_management',
                'line': '10',
                'func': 'action_register_payment'
            })
        # 2) Llamamos al método original para abrir el wizard
        action = super().action_register_payment()
        # Set the mora_pagada_custom_sr value in the wizard context
        if self.is_property_invoice:
            mora_pendiente = self.computed_mora - self.mora_pagada_custom_sr
            action['context'].update({
                'default_mora_pagada_custom_sr': mora_pendiente if mora_pendiente > 0 else 0.0,
                'default_is_property_invoice': self.is_property_invoice
            })
        # 3) Lógica posterior al clic (opcional)
        #    Aquí no hay pago aún, sólo se abre el wizard.

        # Set the mora_pagada_custom_sr value in the payment when created
        def _create_payments(self):
            payments = super().action_create_payments()
            for payment in payments:
                payment.mora_pagada_custom_sr = self.mora_pagada_custom_sr
            return payments
        return action


class srAccountPaymentWizard(models.TransientModel):
    _inherit = 'account.payment.register'

    is_property_invoice = fields.Boolean('Is Property Invoice?')
    mora_pagada_custom_sr = fields.Float(
        string="Monto pagado de mora",
        store=True,
        digits='Product Price',
        default=0.0,
    )
    

class srAccountPayment(models.Model):
    _inherit = 'account.payment'
    is_property_invoice = fields.Boolean('Is Property Invoice?')

    mora_pagada_custom_sr = fields.Float(
        string="Monto pagado de mora",
        store=True,
        digits='Product Price',
        default=0.0,
    )
    