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

class srResUsers(models.Model):
    _inherit = 'res.users'

    @api.model_create_multi
    def create(self, vals_list):
        users = super(srResUsers, self).create(vals_list)
        for user in users:
            # if partner is global we keep it that way
            if user.has_group('sr_property_rental_management.group_landlord'):
                user.partner_id.is_landlord = True
            if user.has_group('sr_property_rental_management.group_agent'):
                user.partner_id.is_agent = True
            if user.has_group('sr_property_rental_management.group_tenant'):
                user.partner_id.is_tenant = True
        return users
    
    def write(self, values):
        res = super(srResUsers, self).write(values)
        if self.has_group('sr_property_rental_management.group_landlord'):
            self.partner_id.is_landlord = True
        else:
            self.partner_id.is_landlord = False
        if self.has_group('sr_property_rental_management.group_agent'):
            self.partner_id.is_agent = True
        else:
            self.partner_id.is_agent = False
        if self.has_group('sr_property_rental_management.group_tenant'):
            self.partner_id.is_tenant = True
        else:
            self.partner_id.is_tenant = False


class srResPartner(models.Model):
    _inherit = 'res.partner'

    is_landlord = fields.Boolean('Is Landlord?')
    is_agent = fields.Boolean('Is Agent?')
    is_tenant = fields.Boolean('Is Tenant')
    settled_commission_count = fields.Integer(compute='_compute_settled_commission_count', string='Tenancy Agreement Count')

    def _compute_settled_commission_count(self):
        settled_commission_ids = self.env['sr.property.agent.commission.settlement'].search([('agent_id','=',self.id)])
        self.settled_commission_count = len(settled_commission_ids)

    def action_view_settled_commission(self):
        self.ensure_one()
        action = self.env["ir.actions.actions"]._for_xml_id("sr_property_rental_management.sr_property_agent_commission_settlement_action")
        action['domain'] = [
            ('agent_id', '=', self.id)
        ]
        return action
