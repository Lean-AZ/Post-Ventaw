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


class srTenancyAgreement(models.Model):
    _name = 'sr.tenancy.agreement'
    _inherit = ['portal.mixin', 'mail.thread', 'mail.activity.mixin', 'utm.mixin']

    @api.depends('property_id', 'agreement_start_date', 'agreement_duration', 'agreement_duration_type')
    def _compute_amount_all(self):
        for order in self:
            num_months = 0
            if order.agreement_start_date and order.agreement_duration and order.agreement_duration_type:
                if order.agreement_duration_type == 'month':
                    a = order.agreement_expiry_date = order.agreement_start_date + relativedelta(months=order.agreement_duration)
                    c = a
                    new_date = a - datetime.timedelta(days = 1)
                    order.agreement_expiry_date = new_date
                else:
                    order.agreement_expiry_date = order.agreement_start_date + relativedelta(years=order.agreement_duration)
                num_months = (order.agreement_expiry_date.year - order.agreement_start_date.year) * 12 + (order.agreement_expiry_date.month - order.agreement_start_date.month )
                difference = relativedelta(order.agreement_expiry_date, order.agreement_start_date)
            else:
                order.agreement_expiry_date = False
                
            if order.property_id.property_type == 'rent':
                commission = 0
                if order.commission_type == 'percentage':
                    commission = (num_months * order.property_id.property_rent_price) * (order.agent_commission / 100)
                else:
                    commission = order.agent_commission
                if order.maintenance_interval_type == "month":
                    maintenance_charge = order.property_id.property_maintenance_charge * num_months
                else:
                    if difference.years > 1:
                        maintenance_charge = order.property_id.property_maintenance_charge * difference.years
                    else:
                        maintenance_charge = order.property_id.property_maintenance_charge * 1
                    
                order.update({
                    'total_price': num_months * order.property_id.property_rent_price,
                    'total_maintenance':maintenance_charge,
                    'commission_price':commission,
                    'final_price' : (num_months * order.property_id.property_rent_price) + commission + maintenance_charge
                })
            elif order.property_id.property_type == 'sale':
                if order.commission_type == 'percentage':
                    commission = (order.property_sale_price) * (order.agent_commission / 100)
                else:
                    commission = order.agent_commission
                order.update({
                    'total_price': order.property_sale_price,
                    'total_maintenance':order.maintenance_charge,
                    'commission_price':commission,
                    'final_price' : commission + order.maintenance_charge + order.property_sale_price
                })
            else:
                order.update({
                    'total_price': 0,
                    'total_maintenance':0,
                    'commission_price':0,
                    'final_price' : 0
                })
    
    @api.onchange('agreement_start_date', 'agreement_duration', 'agreement_duration_type')
    def calculate_agreement_expiry_date(self):
        if self.agreement_start_date:

            if self.agreement_start_date < datetime.datetime.today().date():
                    raise UserError(_('Please set proper agreement start date'))

    @api.depends('company_id')
    def _compute_currency_id(self):
        main_company = self.env['res.company']._get_main_company()
        for template in self:
            template.currency_id = template.company_id.sudo().currency_id.id or main_company.currency_id.id

    name = fields.Char(string='Tenant Agreement Reference', required=True, copy=False, readonly=True, index=True, default=lambda self: _('New'))
    agreement_date = fields.Date(string='Agreement Date', required=True, readonly=True, copy=False, default=fields.Datetime.now, index=True, tracking=1, help="Creation date of tenant agreement.")
    agreement_duration = fields.Integer('Agreement Duration', index=True, tracking=2)
    agreement_duration_type = fields.Selection([('month', 'Month'), ('year', 'year'), ('one_time', 'One Time')], 'Agreement Duration Type', default="month", index=True, tracking=3)
    agreement_start_date = fields.Date(string='Agreement Start From', copy=False) 
    agreement_expiry_date = fields.Date(string='Agreement Expire On', copy=False, compute='_compute_amount_all', store=True, compute_sudo=True)
    property_id = fields.Many2one('product.product', 'Property', required=True, domain="[('is_property','=', True),('state','=', 'available')]", index=True, tracking=4)
    property_type = fields.Selection([('sale', 'Sale'), ('rent', 'Rent')], string="Property For", related="property_id.property_type", store=True)
    property_rent = fields.Float('Rent', related="property_id.property_rent_price", store=True)
    property_sale_price = fields.Float('Sale Price', related="property_id.property_sale_price", store=True)
    agent_id = fields.Many2one('res.partner')
    agent_payment = fields.Integer(string='Payment')
    commission_type = fields.Selection([('fixed', 'Fixed'), ('percentage', 'Percentage')], string="Commission Type", related="property_id.property_agent_commission_type", store=True)
    agent_commission = fields.Float('Commission', related="property_id.property_agent_commission", currency_field='currency_id', store=True)
    landloard_id = fields.Many2one('res.partner', related="property_id.property_landlord_id", store=True)
    company_id = fields.Many2one('res.company', 'Company', required=True, readonly=True,
        default=lambda self: self.env.company)
    currency_id = fields.Many2one('res.currency', string="Currency", compute='_compute_currency_id')
    total_price = fields.Monetary('Total Price', compute='_compute_amount_all', store=True)
    commission_price = fields.Monetary('Commission', compute='_compute_amount_all', store=True)
    final_price = fields.Monetary('Final Price', compute='_compute_amount_all', store=True)
    total_maintenance = fields.Monetary('Total Maintenance', compute='_compute_amount_all', store=True)
    maintenance_charge = fields.Float('Maintenance Charge', related="property_id.property_maintenance_charge", currency_field='currency_id', store=True)
    maintenance_interval_type = fields.Selection([('month', 'Monthly'), ('year', 'Yearly'), ('one_time', 'One Time')], string="Maintenance Interval ", related="property_id.property_maintenance_interval_type", store=True)
    tenant_id = fields.Many2one('res.partner', string="Tenant", required=True)
    payment_option = fields.Selection([('single', 'Single Payment'), ('installment', 'Installments')], string="Payments Option", default='single')
    partial_payment_id = fields.Many2one('sr.property.partial.payment', 'Installments')
    state = fields.Selection([
        ('new', 'New'),
        ('confirm', 'Confirmed'),
        ('running', 'Running'),
        ('expired', 'Expired'),
        ('invoiced', 'Invoiced'),
        ], string='Status', readonly=True, copy=False, index=True, track_visibility="onchange", tracking=5, default='new')

    # @api.onchange('agreement_date')
    # def _onchange_agreement_date(self):
    #     for rec in self:
    #         rec.agreement_date = rec.agreement_date.strftime("%d %b, %Y")

    def action_create_invoice(self):
        if self.property_type != 'sale':
            raise UserError(_('This method can not called with rent property type'))
        journal_id = self.env['account.move']._search_default_journal(journal_types=['sale'])
        accounts = self.property_id.product_tmpl_id.get_product_accounts()
        if self.payment_option == 'single':
            self.env['account.move'].create({
                            'partner_id':self.tenant_id.id,
                            'invoice_date':datetime.datetime.today().date(),
                            'is_property_invoice': True,
                            'property_id': self.property_id.id,
                            'move_type':'out_invoice',
                            'tenancy_agreement':self.id,
                            'journal_id':journal_id.id,
                            'invoice_line_ids':
                                    [(0, 0, {
                            'product_id':self.property_id.id,
                            'name': self.property_id.name + "Property Sold",
                            'quantity':1,
                            'price_unit':self.total_price,
                            'account_id': accounts['income'].id,
                                }),
                            (0, 0, {
                                'product_id':self.property_id.id,
                                'name': self.property_id.name + "Property Maintenance",
                                'quantity':1,
                                'price_unit':self.total_maintenance,
                                'account_id': accounts['income'].id,
                            })
                                    
                                    ]
                            })
        else:
            for i in range(0, self.partial_payment_id.number_of_installments):
                if i == 0:
                    self.env['account.move'].create({
                                'partner_id':self.tenant_id.id,
                                'invoice_date':datetime.datetime.today().date(),
                                'is_property_invoice': True,
                                'property_id': self.property_id.id,
                                'move_type':'out_invoice',
                                'tenancy_agreement':self.id,
                                'journal_id':journal_id.id,
                                'invoice_line_ids':
                                        [(0, 0, {
                                'product_id':self.property_id.id,
                                'name': "Installment " + str(i + 1) + ":" + self.property_id.name + "Property Sold",
                                'quantity':1,
                                'price_unit':self.total_price / self.partial_payment_id.number_of_installments,
                                'account_id': accounts['income'].id,
                                    }),
                                (0, 0, {
                                    'product_id':self.property_id.id,
                                    'name': self.property_id.name + "Property Maintenance",
                                    'quantity':1,
                                    'price_unit':self.total_maintenance,
                                    'account_id': accounts['income'].id,
                                })
                                        
                                        ]
                                })
                else:
                    self.env['account.move'].create({
                                'partner_id':self.tenant_id.id,
                                'invoice_date':datetime.datetime.today().date(),
                                'is_property_invoice': True,
                                'property_id': self.property_id.id,
                                'move_type':'out_invoice',
                                'tenancy_agreement':self.id,
                                'journal_id':journal_id.id,
                                'invoice_line_ids':
                                        [(0, 0, {
                                'product_id':self.property_id.id,
                                'name': "Installment " + str(i + 1) + ":" + self.property_id.name + "Property Sold",
                                'quantity':1,
                                'price_unit':self.total_price / self.partial_payment_id.number_of_installments,
                                'account_id': accounts['income'].id,
                                    })]
                                })
        self.env['sr.property.agent.commission.lines'].create({
                    'name':self.env['ir.sequence'].next_by_code('agent.commission.line.sequence', sequence_date=fields.Datetime.context_timestamp(self, fields.Datetime.to_datetime(datetime.datetime.today().date()))),
                    'tenancy_agreement_id':self.id,
                    'date': datetime.datetime.today().date(),
                    'commission_amount':self.commission_price
                    })
        self.state = 'invoiced'

    def action_confirm(self):
        if self.property_id.state in ['rented', 'sold']:
            raise UserError(_('Sorry! You are late. Someone has already occupy this property.'))
        if self.property_id.state == 'draft':
            raise UserError(_('This property is not confirmed yet by administrator.'))
        self.write({
            'state':'confirm',
            'name': self.env['ir.sequence'].next_by_code('tenancy.agreement.sequence', sequence_date=fields.Datetime.context_timestamp(self, fields.Datetime.to_datetime(self.agreement_date)))
            })
        if self.property_type == 'sale':
            self.property_id.state = 'sold'
        else:
            self.property_id.state = 'rented'
        self.property_id.write({
            'current_user_id':self.tenant_id.id,
            'reservation_history_ids':[(4,self.tenant_id.id)]
            })
        return

    def check_tenancy_agreement_validity(self):
        print ("============datetime.datetime.today().date()",datetime.datetime.today().date())
        start_agreement = self.search([('agreement_start_date', '=', datetime.datetime.today().date()), ('state', '=', 'confirm'),('property_type', '=', 'rent')])
        expiry_agreement = self.search([('agreement_expiry_date', '=', datetime.datetime.today().date()), ('state', '=', 'running')])
        print ("======start_agreement",start_agreement,expiry_agreement)
        if expiry_agreement:
            for record in expiry_agreement:
                record.state = 'expired'
                record.property_id.write({
                    'state':'available',
                    'current_user_id':False
                    })
        if start_agreement:
            for record in start_agreement:
                record.state = 'running'
                if record.property_type == 'rent':
                    if record.agreement_duration_type == 'year':
                        month = 12 * record.agreement_duration
                    else:
                        month = record.agreement_duration
                    for i in range(0, month):
                        journal_id = self.env['account.move']._search_default_journal(journal_types=['sale'])
                        inv_id = self.env['account.move'].create({
                            'partner_id':record.tenant_id.id,
                            'invoice_date':record.agreement_start_date + relativedelta(months=record.agreement_duration),
                            'is_property_invoice': True,
                            'property_id': record.property_id.id,
                            'move_type':'out_invoice',
                            'tenancy_agreement':record.id,
                            'journal_id':journal_id.id
                            })
                        fiscal_position = inv_id.fiscal_position_id
                        accounts = record.property_id.product_tmpl_id.get_product_accounts(fiscal_pos=fiscal_position)
                        inv_id.write({
                            'invoice_line_ids':
                        [(0, 0, {
                            'product_id':record.property_id.id,
                            'name': "Month" + str(i + 1) + ":" + record.property_id.name + "Property Rent",
                            'quantity':1,
                            'price_unit':record.property_rent,
                            'move_id':inv_id.id,
                            'account_id': accounts['income'].id,
                            })]
                            })
                        if record.maintenance_interval_type == 'year' and i % 12 == 0:
                            inv_id.write({
                            'invoice_line_ids':
                        [(0, 0, {
                                'product_id':record.property_id.id,
                                'name': record.property_id.name + "Property Maintenance",
                                'quantity':1,
                                'price_unit':record.maintenance_charge,
                                'move_id':inv_id.id,
                                'account_id': accounts['income'].id,
                                })]
                                })
                        if record.maintenance_interval_type == 'month':
                            inv_id.write({
                            'invoice_line_ids':
                        [(0, 0, {
                                'product_id':record.property_id.id,
                                'name': record.property_id.name + "Property Maintenance",
                                'quantity':1,
                                'price_unit':record.maintenance_charge,
                                'move_id':inv_id.id,
                                'account_id': accounts['income'].id,
                                })]
                                })
                self.env['sr.property.agent.commission.lines'].create({
                    'name':self.env['ir.sequence'].next_by_code('agent.commission.line.sequence', sequence_date=fields.Datetime.context_timestamp(self, fields.Datetime.to_datetime(datetime.datetime.today().date()))),
                    'tenancy_agreement_id':record.id,
                    'date': datetime.datetime.today().date(),
                    'commission_amount':record.commission_price
                    })
                
