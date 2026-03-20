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
from datetime import date
from odoo.exceptions import UserError

class srAccountMoveLine(models.Model):
    _inherit = 'account.move.line'
    
    tenancy_agreement = fields.Many2one('sr.tenancy.agreement', 'Agreement')

class srAccountMove(models.Model):
    _inherit = 'account.move'

    commission_line_id = fields.Many2one(
        'sr.property.agent.commission.lines',
        string="Comisión (legacy)",
        help="Campo legacy; usar Líneas de comisión vinculadas.",
    )
    commission_line_ids = fields.Many2many(
        comodel_name='sr.property.agent.commission.lines',
        relation='account_move_commission_rel',
        column1='move_id',
        column2='commission_line_id',
        string="Líneas de comisión vinculadas",
        help="Comisiones de agente a las que aplica esta factura. Solo se permiten líneas cuyo agente (o agentes de la estructura) coincida con el proveedor de la factura.",
    )
    commission_line_line_ids = fields.Many2many(
        comodel_name='sr.property.agent.commission.lines',
        relation='account_move_commission_rel',
        column1='move_id',
        column2='commission_line_id',
        string="Líneas de comisión vinculadas",
        help="Comisiones de agente a las que aplica esta factura. Solo se permiten líneas cuyo agente (o agentes de la estructura) coincida con el proveedor de la factura.",
    )

    @api.constrains("commission_line_ids", "partner_id")
    def _check_commission_line_partner(self):
        for move in self:
            if not move.partner_id or not move.commission_line_ids:
                continue
            for line in move.commission_line_ids:
                if move.partner_id not in line.allowed_agent_ids:
                    raise UserError(
                        _(
                            "La factura no puede vincularse a la línea de comisión %(name)s: "
                            "el proveedor %(partner)s no es uno de los agentes permitidos para esa comisión.",
                            name=line.name,
                            partner=move.partner_id.name,
                        )
                    )
    is_property_invoice = fields.Boolean('Is Property Invoice?')
    is_ajuste_de_precio = fields.Boolean(string="Es Ajuste de precio?", default=False)
    is_property_addon = fields.Boolean('Es un producto adicional de propiedad?', default=False)
    property_id = fields.Many2one('product.product', string='Property', domain=[('is_property', '=', True)])
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
                payments = self.env['account.payment'].search([
                    ('reconciled_invoice_ids', 'in', move.id)
                ])
                
                mora_paid_temp = sum(payments.mapped('mora_pagada_custom_sr'))
                
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
                    # 'default_capital_pagado_custom_sr': total_capital_pendiente - total_mora_pendiente if total_capital_pendiente - total_mora_pendiente > 0 else 0.0,
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
                    # 'default_capital_pagado_custom_sr': capital_pendiente if capital_pendiente > 0 else 0.0,
                })

        # def _create_payments(self):
        #     payments = super().action_create_payments()
        #     for payment in payments:
        #         payment.mora_pagada_custom_sr = self.mora_pagada_custom_sr
        #     return payments

        return action

    def compute_late_payment_interest(self):
        """
        Cron job para Odoo 17: calcula interés/mora sobre facturas
        de propiedad vencidas y reaplica los pagos anteriores.
        """

        # Parámetros configurables
        interest_percent = 5            # 5% (porcentaje anual o como lo necesites)
        days_to_compute = 30            # prorrateo en 30 días
        # company_ids = self.env['res.company'].search([('calcular_mora_cron', '=', True)]).ids
        company_ids = self.env['res.company'].ids


        today = date.today()

        # 1. Recuperar las compañías de trabajo
        companies = self.env['res.company'].sudo().browse(company_ids)

        for company in companies:
            # 2. Obtener la cuenta de "Ingresos por Mora e intereses clientes"
            advance_account = (
                self.env['account.account']
                .sudo()
                .search([
                    ('name', '=', 'Ingresos por Mora e intereses clientes'),
                    ('company_id', '=', company.id),
                ], limit=1)
            )
            if not advance_account:
                raise UserError(_(
                    'No se encontró la cuenta "Ingresos por Mora e intereses clientes" '
                    'para la compañía %s.' % company.name
                ))
            income_account_id = advance_account.id

            # 3. Buscar facturas vigentes (posted), de tipo cliente, con residual > 0 y vencidas
            invoices = (
                self.search([
                    ('company_id', '=', company.id),
                    ('state', '=', 'posted'),
                    ('move_type', '=', 'out_invoice'),
                    ('amount_residual', '>', 0.0),
                    ('invoice_date_due', '<', today),
                    ('is_property_invoice', '=', True),
                    ('is_ajuste_de_precio', '=', False),
                ])
                .sudo()
            )

            for inv in invoices:
                # Trabajaremos el record sin validar estrictamente movimientos
                inv = inv.with_context(check_move_validity=False)
                due_days = (today - inv.invoice_date_due).days
                if due_days <= 0:
                    continue

                # --- Paso 1: Capturar los pagos parciales ya conciliados ---
                payment_data = []
                # En v17, cada línea de "receivable" que ya esté conciliada
                # tendrá un campo payment_id apuntando al record de account.payment.
                receivable_lines = inv.line_ids.filtered(
                    lambda l: l.account_id.account_type == 'asset_receivable' and l.payment_id
                )
                for line in receivable_lines:
                    payment_data.append({
                        'payment_id': line.payment_id.id,
                        # El monto que se aplicó de ese pago a la factura 
                        # es el valor absoluto de la cantidad reconciliada: 
                        # en la línea de pago, balance será negativo o positivo según débito/crédito.
                        'amount': abs(line.balance),
                    })

                # --- Paso 2: Desconciliar todos esos pagos de la factura ---
                # Quitamos la conciliación de las líneas de tipo "receivable"
                for line in receivable_lines:
                    # `remove_move_reconcile()` es válido en v17
                    line.remove_move_reconcile()

                # --- Paso 3: Calcular o actualizar la línea de "Mora" en la factura ---
                # Filtrar si ya existe una línea cuyo nombre contenga "mora"
                mora_line = inv.invoice_line_ids.filtered(
                    lambda l: l.name and 'mora' in l.name.lower()
                )

                # Monto que aún resta por pagar (sin contar la línea de mora previa)
                amount_due = inv.amount_residual

                if mora_line:
                    # Si ya existía línea de "Mora", la actualizamos
                    mora_total_prev = sum(mora_line.mapped('price_total'))
                    amount_due -= mora_total_prev
                    daily_mora = amount_due * (interest_percent / 100.0) / days_to_compute
                    nueva_mora = daily_mora * due_days
                    mora_line.write({'price_unit': nueva_mora})
                    # Usamos onchange para recalcular impuestos, totales, etc.
                    inv._compute_amount()
                else:
                    # Si no existe, la creamos nueva bajo el nombre "Mora"
                    daily_mora = amount_due * (interest_percent / 100.0) / days_to_compute
                    nueva_mora = daily_mora * due_days
                    inv.write({
                        'invoice_line_ids': [
                            (0, 0, {
                                'name': 'Mora',
                                'quantity': 1.0,
                                'price_unit': nueva_mora,
                                'account_id': income_account_id,
                                'tax_ids': [(6, 0, [])],
                            })
                        ]
                    })
                    # Disparar el onchange para recalcular líneas dinámicas (impuestos, totales, etc.)
                    inv._compute_amount()

                # --- Paso 4: Reaplicar cada pago guardado en payment_data ---
                for p_data in payment_data:
                    payment = self.env['account.payment'].browse(p_data['payment_id'])
                    if not payment:
                        continue

                    # En Odoo 17, para reasignar un pago a una factura,
                    # usamos `js_assign_outstanding_line()` indicando el ID de la línea de move 
                    # que corresponde al registro "receivable" del pago.
                    # Encontramos primero la línea de move de ese pago que sea receivable:
                    payment_move = payment.move_id
                    payment_receivable_line = payment_move.line_ids.filtered(
                        lambda l: l.account_id.account_type == 'asset_receivable'
                    )
                    # Si la concilación se hiciera sobre varias líneas, puedes filtrar
                    # adicionalmente por balance = -p_data['amount'] o algo similar.

                    if payment_receivable_line:
                        try:
                            inv.js_assign_outstanding_line(payment_receivable_line.id)
                        except Exception as e:
                            # Loguear el error pero no interrumpir el proceso de lote
                            log_vals = {
                                'name': 'cron_compute_interest_and_mora',
                                'type': 'server',
                                'dbname': self.env.cr.dbname,
                                'message': _(
                                    'Error reasignando pago %s a factura %s: %s'
                                ) % (payment.name, inv.name, str(e)),
                                'level': 'ERROR',
                                'path': 'cron_interest.py',
                                'func': '_cron_compute_interest_and_mora',
                            }
                            self.env['ir.logging'].sudo().create(log_vals)
                            continue

        return True


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

    def action_create_payments(self):
        # Call parent method - it returns True/False, not payments
        result = super().action_create_payments()
        
        # Since the parent method returns a boolean, we need to find the created payments
        # We'll use the wizard's context to identify the payments
        if result and self.is_property_invoice:
            # Find payments created for this wizard session
            # We can identify them by looking for recent payments with the same amount and date
            payments = self.env['account.payment'].search([
                ('amount', '=', self.amount),
                ('date', '=', self.payment_date),
                ('payment_method_line_id', '=', self.payment_method_line_id.id),
            ], order='id desc', limit=1)
            
            if payments:
                for payment in payments:
                    payment.capital_pagado_custom_sr = self.capital_pagado_custom_sr
                    payment.mora_pagada_custom_sr = self.mora_pagada_custom_sr
                    payment.is_property_invoice = self.is_property_invoice
        
        return result


class srAccountPayment(models.Model):
    _inherit = 'account.payment'
    is_property_invoice = fields.Boolean('Is Property Invoice?')
    is_reserva = fields.Boolean('Es Pago de Reserva?', default=False)


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

    monto_en_rd = fields.Float(
        string="Monto en RD",
        store=True,
        digits='Product Price',
        default=0.0,
        compute='compute_monto_en_rd',
    )

    metodo_de_pago = fields.Selection(
        string="Método de Pago",
        selection=[
            ('efectivo', 'Efectivo'),
            ('deposito', 'Depósito'),
            ('transferencia', 'Transferencia'),
        ],
        default='transferencia',
    )

    numero_de_referencia = fields.Char(
        string="Número de Referencia o Comprobante de operación",
        default='',
        tracking=True,
    )

    banco_emisor = fields.Many2one(
        'res.bank',
        string="Banco Emisor",
        tracking=True,
    )

    banco_receptor = fields.Many2one(
        'res.bank',
        string="Banco Receptor",
        tracking=True,
    )

    @api.depends('amount')
    def compute_monto_en_rd(self):
        for payment in self:
            if (
                'apply_manual_currency_exchange' in payment._fields
                and 'manual_currency_exchange_rate' in payment._fields
                and payment.apply_manual_currency_exchange
            ):
                payment.monto_en_rd = payment.amount * payment.manual_currency_exchange_rate
            else:
                payment.monto_en_rd = payment.amount

class AccountInvoiceReport(models.Model):
    _inherit = 'account.invoice.report'

    amount_total_in_currency_signed = fields.Float(
        string='Total Facturado',
        readonly=True,
        group_operator='sum'
    )

    amount_residual = fields.Float(
        string='Total Pendiente',
        readonly=True,
        group_operator='sum'
    )

    amount_paid = fields.Float(
        string='Total Pagado',
        readonly=True,
        store=True,
        group_operator='sum'
    )

    computed_mora = fields.Float(
        string='Mora Computada',
        readonly=True,
        store=True,
        group_operator='sum'
    )

    mora_pagada_custom_sr = fields.Float(
        string='Mora Pagada',
        readonly=True,
        store=True,
        group_operator='sum'
    )

    def _select(self):
        return super()._select() + ", move.amount_total_in_currency_signed, move.amount_residual, (move.amount_total_in_currency_signed - move.amount_residual) as amount_paid, move.computed_mora, move.mora_pagada_custom_sr"