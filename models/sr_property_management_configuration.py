# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) Sitaram Solutions (<https://sitaramsolutions.in/>).
#
#    For Module Support : info@sitaramsolutions.in  or Skype : contact.hiren1188
#
##############################################################################

from odoo import models, fields, _


class srPropertyCustomPartialPaymentLines(models.Model):
    _name = 'sr.property.custom.partial.payment.lines'
    partial_payment_id = fields.Many2one('sr.property.partial.payment', string="Partial Payment")
    date = fields.Date("Date")
    amount = fields.Float("Amount", digits=(16, 3), required=True)
class srPropertyPartialPayment(models.Model):
    _name = 'sr.property.partial.payment'

    name = fields.Char('Name', required=True)
    number_of_installments = fields.Integer("No of Installments", required=True)
    is_custom = fields.Boolean("Personalizado", default=False, store=True)
    custom_partial_payment_lines = fields.One2many('sr.property.custom.partial.payment.lines', 'partial_payment_id', string="Custom Partial Payment Lines")

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




