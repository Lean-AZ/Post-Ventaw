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

class srAccountMove(models.Model):
    _inherit = 'account.move.line'
    
    tenancy_agreement = fields.Many2one('sr.tenancy.agreement', 'Agreement')

class srAccountMove(models.Model):
    _inherit = 'account.move'

    is_property_invoice = fields.Boolean('Is Property Invoice?')
    property_id = fields.Many2one('product.product', 'Property')
    tenancy_agreement = fields.Many2one('sr.tenancy.agreement', string="Tenancy Agreement")
    is_property_commission_bill = fields.Boolean('Is Property Commission Invoice?')

