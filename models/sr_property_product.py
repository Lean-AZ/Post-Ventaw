# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) Sitaram Solutions (<https://sitaramsolutions.in/>).
#
#    For Module Support : info@sitaramsolutions.in  or Skype : contact.hiren1188
#
##############################################################################

from odoo import models, fields, api,  _
from odoo.exceptions import UserError


class srProductProduct(models.Model):
    _inherit = 'product.product'

    def action_confirm(self):
        if self.property_type == 'sale':
            if self.property_sale_price <= 0:
                raise UserError(_('Please enter reasonable property sale price'))
        if self.property_type == 'rent':
            if self.property_rent_price <= 0:
                raise UserError(_('Please enter reasonable property rent price'))
        self.sudo().write({
            'state' : 'available'
        })
        return 

    @api.onchange('property_type')
    def onchage_property_type(self):
        if self.property_type == 'sale':
            self.property_maintenance_interval_type = 'one_time'
        return

    def action_reset_draft(self):
        self.state = 'draft'

    def action_view_property_invoices(self):
        self.ensure_one()
        action = self.env["ir.actions.actions"]._for_xml_id("account.action_move_out_invoice_type")
        action['domain'] = [
            ('move_type', 'in', ('out_invoice', 'out_refund')),
            ('property_id', '=', self.id),
        ]
        action['context'] = {'default_move_type':'out_invoice', 'move_type':'out_invoice', 'journal_type': 'sale'}
        return action
    
    def action_view_tenancy_agreement(self):
        self.ensure_one()
        action = self.env["ir.actions.actions"]._for_xml_id("sr_property_rental_management.sr_property_tenancy_agreement_action")
        action['domain'] = [
            ('property_id', '=', self.id)
        ]
        return action
    

class srPropertytemplate(models.Model):
    _inherit = 'product.template'


    @api.onchange('property_type')
    def onchage_property_type(self):
        if self.property_type == 'sale':
            self.property_maintenance_interval_type = 'one_time'
        return


    is_property = fields.Boolean('Is Property?')
    property_type = fields.Selection([('sale', 'Sale'), ('rent', 'Rent')], string="Property For", default="rent")
    property_sale_price = fields.Float(
        'Property Sales Price', default=1.0,
        digits='Product Price',
        help="Price at which the Property is sold to Tenants.")
    property_rent_price = fields.Float(
        'Property Rent Price', default=1.0,
        digits='Product Price',
        help="Price at which the Property is Rented to Tenants.")
    property_construction_status = fields.Selection([('under_const', 'Under Construction'), ('ready_to_move', 'Ready To Move')], string="Property Status", default="ready_to_move")
    user_id = fields.Many2one('res.users', string="Sales Person", default=lambda self: self.env.user)
    street = fields.Char()
    street2 = fields.Char()
    zip = fields.Char(change_default=True)
    city = fields.Char()
    state_id = fields.Many2one("res.country.state", string='State', ondelete='restrict', domain="[('country_id', '=?', country_id)]")
    country_id = fields.Many2one('res.country', string='Country', ondelete='restrict') 
    property_carpet_area = fields.Float('Carpet Area', default=1)
    property_build_up_area = fields.Float('Build-up Area', default=1)
    property_floor = fields.Integer('Floor', default=1)
    property_badrooms = fields.Integer('Badrooms', default=1)
    property_balconies = fields.Float('Balconies', default=1)
    property_maintenance_charge = fields.Float('Maintenance Charge', default=1)
    property_maintenance_interval_type = fields.Selection([('month', 'Monthly'), ('year', 'Yearly'), ('one_time', 'One Time')], string="Maintenance Interval ", default="month")
    description = fields.Text('Description')
    property_interior_ids = fields.Many2many('sr.property.interior', 'temp_property_interior_rel', 'property_id', 'interior_id', string="Interior")
    property_exterior_ids = fields.Many2many('sr.property.exterior', 'temp_property_exterior_rel', 'property_id', 'exterior_id', string="Exterior")
    property_facade_ids = fields.Many2many('sr.property.facade', 'temp_property_facade_rel', 'property_id', 'facade_id', string="Facade")
    property_amenities_ids = fields.Many2many('sr.property.amenities', 'temp_property_amenities_rel', 'property_id', 'amenities_id', string="Amenities")
    property_neighbourhood_ids = fields.Many2many('sr.property.neighborhood', 'temp_property_neighborhood_rel', 'property_id', 'neighborhood_id', string="Neighborhood")
    property_transportation_ids = fields.Many2many('sr.property.transportation', 'temp_property_transportation_rel', 'property_id', 'transportation_id', string="Transportation")
    property_landscape_ids = fields.Many2many('sr.property.landscape', 'temp_property_landscape_rel', 'property_id', 'landscape_id', string="Landscape")
    property_residential_type_ids = fields.Many2many('sr.property.type', 'temp_property_type_rel', 'property_id', 'type_id', string="Residential Type")
    gas_safety_exp_date = fields.Date('Gas Safety Expiry Date')
    gas_safety_exp_attch = fields.Binary('Gas Safety Expiry Attachment')
    electricity_safety_certificate = fields.Binary('Electricity Safety Certificate Attachment')
    epc = fields.Char('Energy Performance (EPC)')
    property_landlord_id = fields.Many2one('res.partner', string="Landloard")
    property_landlord_email_id = fields.Char(related="property_landlord_id.email", string="Email")
    property_landlord_phone = fields.Char(related="property_landlord_id.phone", string="Phone")
    property_agent_id = fields.Many2one('res.partner', string="Agent")
    property_agent_commission_type = fields.Selection([('fixed', 'Fixed'), ('percentage', 'Percentage')], string="Commission Type", default="fixed")
    property_agent_commission = fields.Float('Commission')
    property_agent_email_id = fields.Char(related="property_agent_id.email", string="Email")
    property_agent_phone = fields.Char(related="property_agent_id.phone", string="Phone")
    state = fields.Selection([
        ('draft', 'Draft'),
        ('available', 'Available'),
        ('rented', 'Rented'),
        ('sold', 'Sold'),
        ], string='Status', readonly=True, copy=False, index=True, track_visibility="onchange")
    property_invoice_count = fields.Integer(compute='_compute_property_invoice_count', string='Property Invoices Count')
    tenancy_agreement_count = fields.Integer(compute='_compute_tenancy_agreement_count', string='Tenancy Agreement Count')
    current_user_id = fields.Many2one('res.partner','Current User')
    reservation_history_ids = fields.Many2many('res.partner',string="Reservation history")

    def action_view_tenancy_agreement(self):
        self.ensure_one()
        action = self.env["ir.actions.actions"]._for_xml_id("sr_property_rental_management.sr_property_tenancy_agreement_action")
        action['domain'] = [
            ('property_id.product_tmpl_id', '=', self.id),
        ]
        return action
    
    def action_view_property_invoices(self):
        self.ensure_one()
        action = self.env["ir.actions.actions"]._for_xml_id("account.action_move_out_invoice_type")
        action['domain'] = [
            ('move_type', 'in', ('out_invoice', 'out_refund')),
            ('property_id.product_tmpl_id', '=', self.id),
        ]
        action['context'] = {'default_move_type':'out_invoice', 'move_type':'out_invoice', 'journal_type': 'sale', 'search_default_unpaid': 1}
        return action

    def _compute_tenancy_agreement_count(self):
        agreement_ids = self.env['sr.tenancy.agreement'].search([('property_id.product_tmpl_id','=',self.id)])
        self.tenancy_agreement_count = len(agreement_ids)
    
    def _compute_property_invoice_count(self):
        invoice_ids = self.env['account.move'].search([('property_id.product_tmpl_id','=',self.id)])
        self.property_invoice_count = len(invoice_ids)

    def action_confirm(self):
        if self.property_type == 'sale':
            if self.property_sale_price <= 0:
                raise UserError(_('Please enter reasonable property sale price'))
        if self.property_type == 'rent':
            if self.property_rent_price <= 0:
                raise UserError(_('Please enter reasonable property rent price'))
        self.sudo().write({
            'state' : 'available',
        })
        return

    def action_reset_draft(self):
        self.state = 'draft'
    
