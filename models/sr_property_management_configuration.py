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

class srPropertyCustomPartialPaymentLines(models.Model):
    _name = 'sr.property.custom.partial.payment.lines'
    partial_payment_id = fields.Many2one('sr.property.partial.payment', string="Partial Payment")
    date = fields.Date("Date", required=True)
    amount = fields.Float("Amount", digits=(16, 3), required=True)

    @api.constrains('amount')
    def _check_amount_positive(self):
        for record in self:
            if record.amount < 0:
                raise ValidationError(_("Amount cannot be negative."))

class srPropertyPartialPayment(models.Model):
    _name = 'sr.property.partial.payment'

    name = fields.Char('Name', required=True)
    number_of_installments = fields.Integer("No of Installments", compute='_compute_number_of_installments', store=True)
    is_custom = fields.Boolean("Personalizado", default=True, store=True)
    custom_partial_payment_lines = fields.One2many('sr.property.custom.partial.payment.lines', 'partial_payment_id', string="Custom Partial Payment Lines")
    property_id = fields.Many2one('product.product', 'Unidad', required=True, domain="[('is_property','=', True),('state','=', 'available')]", index=True, tracking=4)
    property_price = fields.Float(related='property_id.property_sale_price', string='Precio de la unidad', store=True, readonly=True)
    total_custom_payments = fields.Float(compute='_compute_total_custom_payments', string='Financiamiento + Separación', store=True)
    remaining_balance = fields.Float(compute='_compute_remaining_balance', string='Financiamiento', store=True)

    @api.depends('custom_partial_payment_lines')
    def _compute_number_of_installments(self):
        for record in self:
            record.number_of_installments = len(record.custom_partial_payment_lines)

    @api.depends('custom_partial_payment_lines.amount')
    def _compute_total_custom_payments(self):
        for record in self:
            record.total_custom_payments = sum(line.amount for line in record.custom_partial_payment_lines)

    @api.depends('property_price', 'total_custom_payments')
    def _compute_remaining_balance(self):
        for record in self:
            if record.property_price:
                record.remaining_balance = record.property_price - record.total_custom_payments
            else:
                record.remaining_balance = 0.0

    @api.onchange('property_id')
    def _onchange_property_id(self):
        if self.property_id:
            self.name = f"Plan de Pagos - {self.property_id.name}"

class srPropertyType(models.Model):
    _name = 'sr.property.type'

    name = fields.Char('Name', required=True)

class srPropertyInterior(models.Model):
    _name = 'sr.property.interior'

    name = fields.Char('Name', required=True)

class srPropertyExterior(models.Model):
    _name = 'sr.property.exterior'

    name = fields.Char('Name', required=True)

class srPropertyFacade(models.Model):
    _name = 'sr.property.facade'

    name = fields.Char('Name', required=True)

class srPropertyAmenities(models.Model):
    _name = 'sr.property.amenities'

    name = fields.Char('Name', required=True)

class srPropertyNeighborhood(models.Model):
    _name = 'sr.property.neighborhood'

    name = fields.Char('Name', required=True)


class srPropertyTransportation(models.Model):
    _name = 'sr.property.transportation'

    name = fields.Char('Name', required=True)

class srPropertyLandscape(models.Model):
    _name = 'sr.property.landscape'

    name = fields.Char('Name', required=True)




