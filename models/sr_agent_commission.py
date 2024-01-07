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
from odoo.exceptions import UserError, ValidationError
import datetime
from dateutil.relativedelta import relativedelta


class srPropertyAgentCommissionSettlementLines(models.Model):
    _name = 'sr.property.agent.commission.settlement.lines'

    property_id = fields.Many2one('product.product', string="Property")
    tenancy_agreement_id = fields.Many2one('sr.tenancy.agreement', string="Tenancy Agreement")
    date = fields.Date(string='Date', required=True, copy=False, default=fields.Datetime.now)
    currency_id = fields.Many2one('res.currency', string="Currency")
    commission_amount = fields.Float('Commission', currency_field='currency_id')
    commission_settlement_id = fields.Many2one('sr.property.agent.commission.settlement', string="Commission Settlement")
    commission_line = fields.Many2one('sr.property.agent.commission.lines', string="Commission Line Reference")


class srPropertyAgentCommissionSettlement(models.Model):
    _name = 'sr.property.agent.commission.settlement'

    name = fields.Char(string='Commission Settlement Reference', required=True, copy=False, readonly=True, index=True, default=lambda self: _('New'))
    date = fields.Date(string='Date', required=True, copy=False, default=fields.Datetime.now)
    agent_commission_line_ids = fields.One2many('sr.property.agent.commission.settlement.lines', 'commission_settlement_id', string="Commission Settlement Lines")
    agent_id = fields.Many2one('res.partner', 'agent', required=True)
    state = fields.Selection([
        ('new', 'New'),
        ('confirm', 'Confirmed'),
        ('invoiced', 'Invoiced'),
        ], string='Status', readonly=True, copy=False, index=True, track_visibility="onchange", tracking=5, default='new')

#     @api.onchange('agent_id')
#     def onchange_agent_id(self):
#         if self.agent_id:
#             comm_line = self.env['sr.property.agent.commission.lines'].search([('agent_id','=',self.agent_id.id),('is_commission_settled','=',False)])
#             print ("========comm_line",comm_line)
#             self.agent_commission_line_ids = [(6,0,[a.id for a in comm_line])]
#         else:
#             self.agent_commission_line_ids = [(5,)]

    def calculate_agent_commission(self):
        self.agent_commission_line_ids.unlink()
        comm_line = self.env['sr.property.agent.commission.lines'].search([('agent_id', '=', self.agent_id.id), ('is_commission_settled', '=', False)])
        print ("====comm_line", comm_line)
        for line in comm_line:
            self.write({
                'agent_commission_line_ids':[
                    (0, 0, {'property_id': line.property_id.id,
                            'tenancy_agreement_id': line.tenancy_agreement_id.id,
                            'date': line.date,
                            'currency_id':line.currency_id.id,
                            'commission_amount':line.commission_amount,
                            'commission_line':line.id
                            })
                ]
                })
        return

    def action_confirm(self):
        if not self.agent_commission_line_ids:
            raise UserError(_('There is no any commission Lines.\n Please Calculate commission line or contact your administrator'))
        for record in self.agent_commission_line_ids:
            record.commission_line.write({
                'is_commission_settled':True,
                'commission_settlement_id':self.id
                })
        self.write({
            'name' : self.env['ir.sequence'].next_by_code('agent.commission.settlement.sequence', sequence_date=fields.Datetime.context_timestamp(self, fields.Datetime.to_datetime(datetime.datetime.today().date()))),
            'state':'confirm'
            })

    def action_create_invoice(self):
        journal_id = self.env['account.move']._search_default_journal(journal_types=['sale'])
        inv_id = self.env['account.move'].create({
            'partner_id':self.agent_id.id,
            'invoice_date':datetime.datetime.today().date(),
            'is_property_commission_bill': True,
            'move_type':'in_invoice',
            'journal_id':journal_id.id,
            })
        for record in self.agent_commission_line_ids:
            fiscal_position = inv_id.fiscal_position_id
            accounts = record.property_id.product_tmpl_id.get_product_accounts(fiscal_pos=fiscal_position)
            inv_id.write({
                            'invoice_line_ids':
                        [(0, 0, {
                            'product_id':record.property_id.id,
                            'name': record.property_id.name + "Maintenance. Agreement No:" + str(record.tenancy_agreement_id.name),
                            'quantity':1,
                            'price_unit':record.commission_amount,
                            'account_id': accounts['income'].id,
                            'tenancy_agreement':record.tenancy_agreement_id.id,
                            })]
                            })
        self.state = 'invoiced'
        return


class srPropertyAgentCommissionLines(models.Model):
    _name = 'sr.property.agent.commission.lines'

    name = fields.Char(string='Commission Line Reference', required=True, copy=False, readonly=True, index=True, default=lambda self: _('New'))
    property_id = fields.Many2one('product.product', 'Property', required=True, related="tenancy_agreement_id.property_id")
    tenancy_agreement_id = fields.Many2one('sr.tenancy.agreement', 'Agreement', required=True)
    date = fields.Date(string='Date', required=True, copy=False, default=fields.Datetime.now)
    agent_id = fields.Many2one('res.partner', required=True, copy=False, related="tenancy_agreement_id.agent_id")
    commission_type = fields.Selection([('fixed', 'Fixed'), ('percentage', 'Percentage')], string="Commission Type", related="tenancy_agreement_id.commission_type")
    commission_amount = fields.Float('Commission', currency_field='currency_id')
    currency_id = fields.Many2one('res.currency', string="Currency", related="tenancy_agreement_id.currency_id")
    is_commission_settled = fields.Boolean('Is Commission Settled?') 
    commission_settlement_id = fields.Many2one('sr.property.agent.commission.settlement', string="Commission Settlement")
    
