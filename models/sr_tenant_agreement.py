from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
import datetime
from dateutil.relativedelta import relativedelta
import calendar


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
    notario_publico_id = fields.Many2one("res.partner", "Notario Público")
    active = fields.Boolean(string='Active', default=True)
    agreement_date = fields.Date(string='Agreement Date', required=True, readonly=True, copy=False, default=fields.Datetime.now, index=True, tracking=1, help="Creation date of tenant agreement.")
    agreement_duration = fields.Integer('Agreement Duration', index=True, tracking=2)
    agreement_duration_type = fields.Selection([('month', 'Month'), ('year', 'year'), ('one_time', 'One Time')], 'Agreement Duration Type', default="month", index=True, tracking=3)
    agreement_start_date = fields.Date(string='Agreement Start From', copy=False) 
    agreement_expiry_date = fields.Date(string='Agreement Expire On', copy=False, compute='_compute_amount_all', store=True, compute_sudo=True)
    property_id = fields.Many2one('product.product', 'Unidad', required=True, domain="[('is_property','=', True),('state','=', 'available')]", index=True, tracking=4)
    property_type = fields.Selection([('sale', 'Sale'), ('rent', 'Rent')], string="Tipo", related="property_id.property_type", store=True)
    property_rent = fields.Float('Rent', related="property_id.property_rent_price", store=True)
    property_sale_price = fields.Float('Precio de venta', related="property_id.property_sale_price", store=True)
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
    payment_option = fields.Selection([('single', 'Single Payment'), ('installment', 'Installments')], string="Payments Option", default='installment')
    partial_payment_id = fields.Many2one('sr.property.partial.payment', 'Installments',  domain="[('property_id', '=', property_id)]")
    state = fields.Selection([
        ('new', 'New'),
        ('confirm', 'Confirmed'),
        ('running', 'Running'),
        ('expired', 'Expired'),
        ('invoiced', 'Invoiced'),
        ], string='Status', readonly=True, copy=False, index=True, track_visibility="onchange", tracking=5, default='new')
    reserve_amount = fields.Float('Monto De Reserva', currency_field='currency_id', store=True)
    initial_amount = fields.Float('Monto de Separación', currency_field='currency_id', store=True)
    currency_id = fields.Many2one('res.currency', string='Moneda', readonly=True, store=True, related='property_id.currency_id')
    amount_to_finance = fields.Float('Monto Inicial', currency_field='currency_id', store=True)
    gastos_legales = fields.Float('Gastos Legales', currency_field='currency_id', store=True, default=500.0)
    gastos_legales_invoiced = fields.Boolean('Gastos Legales Invoiced', default=False)
    first_installment_date = fields.Date(string='Pago de primer cuota', copy=False, store=True)
    co_tenant_id = fields.Many2one('res.partner', string="Copropietario")
    delivery_date = fields.Date('Fecha de entrega', store=True, related='property_id.delivery_date')
    agent_type = fields.Selection([('interno', 'Interno'), ('externo', 'Externo')], string="Tipo de Agente", default='interno')
    coletilla_notarial = fields.Text('Coletilla Notarial')
    co_owner_relationship = fields.Selection([
        ('casado', 'Casado'),
        ('hermanos', 'Hermanos'),
        ('amigos', 'Amigos'),
        ('persona_juridica', 'Persona Jurídica')
    ], string="Relación con el Co-propietario", help="Select the relationship type between the tenant and the co-owner.")
    financing_amount = fields.Float(
        compute='_compute_financing_details',
        string='Financiamiento',
        store=True
    )

    financed_percentage = fields.Float(
        compute='_compute_financing_details',
        string='Porcentaje Financiado',
        store=True
    )

    formatted_financed_percentage = fields.Char(
        'Porcentaje Financiado',
        compute='_compute_formatted_financed_percentage'
    )

    @api.onchange('partial_payment_id')
    def _onchange_partial_payment_id(self):
        # Ensure that the partial payment ID is set and custom payments are enabled
        if self.partial_payment_id and self.partial_payment_id.is_custom:
            # Access the first custom partial payment line if it exists
            if self.partial_payment_id.custom_partial_payment_lines:
                # Set the initial amount to the first line's amount
                self.initial_amount = self.partial_payment_id.custom_partial_payment_lines[0].amount
                self.amount_to_finance = self.partial_payment_id.total_custom_payments - self.partial_payment_id.custom_partial_payment_lines[0].amount
            else:
                # If there are no lines, set the initial amount to zero
                self.initial_amount = 0.0   

    @api.depends('property_sale_price', 'initial_amount', 'reserve_amount', 'amount_to_finance')
    def _compute_financing_details(self):
        for record in self:
            # Calculate the financing amount
            record.financing_amount = (
                record.property_sale_price - (record.initial_amount + record.amount_to_finance)
            )

            # Calculate the financed percentage based on financing amount
            if record.property_sale_price and record.property_sale_price != 0:
                record.financed_percentage = (
                    float(record.financing_amount) / float(record.property_sale_price) * 100.0
                )
            else:
                record.financed_percentage = 0.0

    # @api.constrains('financed_percentage')
    # def _check_financed_percentage(self):
    #     for record in self:
    #         if record.financed_percentage > 65.0:
    #             raise ValidationError(
    #                  "El porcentaje financiado no puede exceder el 65%. Por favor revise los detalles de financiamiento"
    #             )


    @api.depends('amount_to_finance', 'property_sale_price')
    def _compute_formatted_financed_percentage(self):
        for record in self:
            if record.property_sale_price and record.property_sale_price != 0:
                computed_paid_amount = record.initial_amount + record.amount_to_finance
                financed_percentage = (
                    float(record.property_sale_price - computed_paid_amount) / float(record.property_sale_price) * 100.0
                )
                # Format the percentage to two decimal places as a string
                percentage_str = "{:.2f}".format(financed_percentage)
                # Insert a comma after the first two digits if the string is long enough
                if len(percentage_str) > 2:
                    record.formatted_financed_percentage = percentage_str[:2] + '' + percentage_str[2:]
                else:
                    record.formatted_financed_percentage = percentage_str
            else:
                # Provide a default value for cases where computation cannot be performed
                record.formatted_financed_percentage = "0.00"


    # @api.onchange('agreement_date')
    # def _onchange_agreement_date(self):
    #     for rec in self:
    #         rec.agreement_date = rec.agreement_date.strftime("%d %b, %Y")

    def action_create_invoice(self):
        if self.property_type != 'sale':
            raise UserError(_('This method can not called with rent property type'))
        journal_id = self.env['account.journal'].search([('name', 'ilike', 'no fiscal')], limit=1)
        
        if not journal_id:
            journal_id = self.env['account.move']._search_default_journal(journal_types=['sale'])
        accounts = self.property_id.product_tmpl_id.get_product_accounts()
        advance_account = self.env['account.account'].search([('name', '=', 'Avance recibido de clientes')], limit=1)
        # Fall back to the default income account if not found
        income_account_id = advance_account.id if advance_account else accounts['income'].id
        if self.payment_option == 'single':
            self.env['account.move'].create({
                            'partner_id':self.tenant_id.id,
                            'invoice_date':datetime.datetime.today().date(),
                            'invoice_date_due':datetime.datetime.today().date() + relativedelta(days=30),
                            'is_property_invoice': True,
                            'property_id': self.property_id.id,
                            'move_type':'out_invoice',
                            'tenancy_agreement':self.id,
                            'journal_id':journal_id.id,
                            'currency_id':self.currency_id.id,
                            'invoice_line_ids':
                                    [(0, 0, {
                            'product_id':self.property_id.id,
                            'name': self.property_id.name + "Property Sold",
                            'quantity':1,
                            'price_unit':self.total_price,
                            'account_id': income_account_id,
                                }),
                            (0, 0, {
                                'product_id':self.property_id.id,
                                'name': self.property_id.name + "Property Maintenance",
                                'quantity':1,
                                'price_unit':self.total_maintenance,
                                'account_id': income_account_id,
                            })
                                    
                                    ]
                            })
        else:
            for i in range(0, self.partial_payment_id.number_of_installments):
                if i == 0:
                    self.env['account.move'].create({
                                'partner_id':self.tenant_id.id,
                                'auto_post': True,  
                                'invoice_date':datetime.datetime.today().date(),
                                'invoice_date_due':datetime.datetime.today().date() + relativedelta(days=30),
                                'is_property_invoice': True,
                                'property_id': self.property_id.id,
                                'move_type':'out_invoice',
                                'tenancy_agreement':self.id,
                                'journal_id':journal_id.id,
                                'currency_id':self.currency_id.id,
                                'invoice_line_ids':
                                        [(0, 0, {
                                'product_id':self.property_id.id,
                                'name': "Installment " + str(i + 1) + ":" + self.property_id.name + "Property Sold",
                                'quantity':1,
                                'price_unit':self.total_price / self.partial_payment_id.number_of_installments,
                                'account_id': income_account_id,
                                    }),
                                (0, 0, {
                                    'product_id':self.property_id.id,
                                    'name': self.property_id.name + "Property Maintenance",
                                    'quantity':1,
                                    'price_unit':self.total_maintenance,
                                    'account_id': income_account_id,
                                })
                                        
                                        ]
                                })
                else:
                    self.env['account.move'].create({
                                'partner_id':self.tenant_id.id,
                                'auto_post': True,
                                'invoice_date':datetime.datetime.today().date(),
                                'invoice_date_due':datetime.datetime.today().date() + relativedelta(days=30),
                                'is_property_invoice': True,
                                'property_id': self.property_id.id,
                                'move_type':'out_invoice',
                                'tenancy_agreement':self.id,
                                'journal_id':journal_id.id,
                                'currency_id':self.currency_id.id,
                                'invoice_line_ids':
                                        [(0, 0, {
                                'product_id':self.property_id.id,
                                'name': "Installment " + str(i + 1) + ":" + self.property_id.name + "Property Sold",
                                'quantity':1,
                                'price_unit':self.total_price / self.partial_payment_id.number_of_installments,
                                'account_id': income_account_id,
                                    })]
                                })
        self.env['sr.property.agent.commission.lines'].create({
                    'name':self.env['ir.sequence'].next_by_code('agent.commission.line.sequence', sequence_date=fields.Datetime.context_timestamp(self, fields.Datetime.to_datetime(datetime.datetime.today().date()))),
                    'tenancy_agreement_id':self.id,
                    'date': datetime.datetime.today().date(),
                    'commission_amount':self.commission_price
                    })
        self.state = 'invoiced'

    def action_create_invoice_civiltec(self):
        if self.property_type != 'sale':
            raise UserError(_('This method can not called with rent property type'))
        journal_id = self.env['account.journal'].search([('name', 'ilike', 'no fiscal')], limit=1)

        if not journal_id:
            journal_id = self.env['account.move']._search_default_journal(journal_types=['sale'])

        accounts = self.property_id.product_tmpl_id.get_product_accounts()

        advance_account = self.env['account.account'].search([('name', '=', 'Avance recibido de clientes')], limit=1)

        # Fall back to the default income account if not found
        income_account_id = advance_account.id if advance_account else accounts['income'].id

        if self.payment_option == 'single':
            self.env['account.move'].create({
                            'partner_id':self.tenant_id.id,
                            'auto_post': True,
                            'invoice_date':datetime.datetime.today().date(),
                            'invoice_date_due':datetime.datetime.today().date() + relativedelta(days=30),
                            'is_property_invoice': True,
                            'property_id': self.property_id.id,
                            'move_type':'out_invoice',
                            'tenancy_agreement':self.id,
                            'journal_id':journal_id.id,
                            'currency_id': self.currency_id.id,
                            'invoice_line_ids':
                                    [(0, 0, {
                            'product_id':self.property_id.id,
                            'name': self.property_id.name + " Saldo",
                            'quantity':1,
                            'price_unit':self.total_price,
                            'account_id': income_account_id,
                                })]
                            })
        else:
            if not self.partial_payment_id.is_custom:
                self.env['account.move'].create({
                 'partner_id':self.tenant_id.id,
                 'auto_post': True,
                 'invoice_date':datetime.datetime.today().date(),
                 'invoice_date_due':datetime.datetime.today().date() + relativedelta(days=30),
                 'is_property_invoice': True,
                 'property_id': self.property_id.id,
                 'move_type':'out_invoice',
                 'tenancy_agreement':self.id,
                 'journal_id':journal_id.id,
                 'currency_id': self.currency_id.id,
                 'invoice_line_ids':
                         [(0, 0, {
                 'product_id':self.property_id.id,
                 'name': "Monto de Reserva:" + self.property_id.name,
                 'quantity':1,
                 'price_unit': self.initial_amount,
                 'account_id': income_account_id,
                     })]
                 })
            installment_date = self.first_installment_date
            if self.partial_payment_id.is_custom:
                amount = 0
                for index, line in enumerate(self.partial_payment_id.custom_partial_payment_lines, start=1):
                    self.env['account.move'].create({
                                'partner_id':self.tenant_id.id,
                                'auto_post': True,
                                'invoice_date':line.date,
                                'invoice_date_due':line.date + relativedelta(days=30),
                                'is_property_invoice': True,
                                'property_id': self.property_id.id,
                                'move_type':'out_invoice',
                                'tenancy_agreement':self.id,
                                'journal_id':journal_id.id,
                                'currency_id': self.currency_id.id,
                                'invoice_line_ids':
                                        [(0, 0, {
                                'product_id':self.property_id.id,
                                'name': f"Cuota {index}: {self.property_id.name}",
                                'quantity':1,
                                'price_unit':line.amount,
                                'account_id': income_account_id,
                                    })]
                                })
                    amount += line.amount

                # if (self.total_price - self.reserve_amount - self.initial_amount - amount) > 0:
                #     self.env['account.move'].create({
                #         'partner_id':self.tenant_id.id,
                #         'invoice_date': self.property_id.delivery_date,
                #         'is_property_invoice': True,
                #         'property_id': self.property_id.id,
                #         'move_type':'out_invoice',
                #         'tenancy_agreement':self.id,
                #         'journal_id':journal_id.id,
                #         'currency_id': self.currency_id.id,
                #         'invoice_line_ids':
                #                 [(0, 0, {
                #         'product_id':self.property_id.id,
                #         'name': "Cuota Final :" + self.property_id.name,
                #         'quantity':1,
                #         'price_unit': self.total_price - self.reserve_amount - self.initial_amount - amount,
                #         'account_id': income_account_id,
                #             })]
                #         })
                self.env['account.move'].create({
                    'partner_id':self.tenant_id.id,
                    'auto_post': True,
                    'invoice_date': self.property_id.delivery_date,
                    'invoice_date_due': self.property_id.delivery_date + relativedelta(days=30),
                    'is_property_invoice': True,
                    'property_id': self.property_id.id,
                    'move_type':'out_invoice',
                    'tenancy_agreement':self.id,
                    'journal_id':journal_id.id,
                    'currency_id': self.currency_id.id,
                    'invoice_line_ids':
                            [(0, 0, {
                    'product_id':self.property_id.id,
                    'name': "Cuota Final :" + self.property_id.name,
                    'quantity':1,
                    'price_unit': self.property_id.property_sale_price - amount,
                    'account_id': income_account_id,
                        })]
                    })
            else:
                def months_between_dates(initial_date_str, final_date_str):
                    initial_date = initial_date_str
                    final_date = final_date_str
                    # Calculate the difference in months
                    month_diff = (final_date.year - initial_date.year) * 12 + final_date.month - initial_date.month
                    # Adjust if the final date's day is less than the initial date's day
                    if final_date.day < initial_date.day:
                        month_diff -= 1
                    return month_diff

                months_until_last_installment = months_between_dates(self.first_installment_date, self.delivery_date)

                regular_installment_amount = self.amount_to_finance / months_until_last_installment
                allocated_amount = 0
                for i in range(0, months_until_last_installment):
                    if i == months_until_last_installment - 1:
                        installment_amount = self.amount_to_finance - allocated_amount
                    else:
                        installment_amount = regular_installment_amount
                        allocated_amount += installment_amount
                    self.env['account.move'].create({
                                'partner_id':self.tenant_id.id,
                                'auto_post': True,
                                'invoice_date': installment_date,
                                'invoice_date_due': installment_date + relativedelta(days=30),
                                'is_property_invoice': True,
                                'property_id': self.property_id.id,
                                'move_type':'out_invoice',
                                'tenancy_agreement':self.id,
                                'journal_id':journal_id.id,
                                'currency_id': self.currency_id.id,
                                'invoice_line_ids':
                                        [(0, 0, {
                                'product_id':self.property_id.id,
                                'name': "Inicial Cuota #" + str(i + 1) + ":" + self.property_id.name,
                                'quantity':1,
                                'price_unit':installment_amount,
                                'account_id': income_account_id,
                                    })]
                                })
                    next_month = installment_date + relativedelta(months=1)
                    last_day_of_next_month = next_month.replace(day=calendar.monthrange(next_month.year, next_month.month)[1])
                    installment_date = last_day_of_next_month
                    invoice_date_due = installment_date + relativedelta(days=30)

                self.env['account.move'].create({
                 'partner_id':self.tenant_id.id,
                 'auto_post': True,
                 'invoice_date':installment_date,
                 'invoice_date_due':invoice_date_due + relativedelta(days=30),
                 'is_property_invoice': True,
                 'property_id': self.property_id.id,
                 'move_type':'out_invoice',
                 'tenancy_agreement':self.id,
                 'journal_id':journal_id.id,
                 'currency_id': self.currency_id.id,
                 'invoice_line_ids':
                         [(0, 0, {
                 'product_id':self.property_id.id,
                 'name': "Cuota Final :" + self.property_id.name,
                 'quantity':1,
                 'price_unit': self.total_price - self.amount_to_finance - self.reserve_amount - self.initial_amount,
                 'account_id': income_account_id,
                     })]
                 })
        self.env['sr.property.agent.commission.lines'].create({
                    'name':self.env['ir.sequence'].next_by_code('agent.commission.line.sequence', sequence_date=fields.Datetime.context_timestamp(self, fields.Datetime.to_datetime(datetime.datetime.today().date()))),
                    'tenancy_agreement_id':self.id,
                    'date': datetime.datetime.today().date(),
                    'commission_amount':self.commission_price
                    })
        self.property_id.state = 'sold'
        self.state = 'invoiced'

    def cancel_booked_property(self):
        if self.property_type != 'sale':
            raise UserError(_('This method can not called with rent property type'))
        self.property_id.state = 'available'
        self.state = 'expired'

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
            raise UserError(_('Primero hay que separar la propiedad'))
        if self.property_type == 'booked':
            self.property_id.state = 'sold'
        else:
            self.property_id.state = 'rented'
        self.property_id.write({
            'current_user_id':self.tenant_id.id,
            'reservation_history_ids':[(4,self.tenant_id.id)]
            })
        return

    def action_booked(self):
        if self.property_id.state in ['rented', 'sold']:
            raise UserError(_('Sorry! You are late. Someone has already occupy this property.'))
        if self.property_id.state == 'draft':
            raise UserError(_('This property is not confirmed yet by administrator.'))
        self.write({
            'state':'confirm',
            'name': self.env['ir.sequence'].next_by_code('tenancy.agreement.sequence', sequence_date=fields.Datetime.context_timestamp(self, fields.Datetime.to_datetime(self.agreement_date)))
            })
        if self.property_type == 'sale':
            self.property_id.state = 'booked'
            journal_id = self.env['account.journal'].search([('name', 'ilike', 'no fiscal')], limit=1)
        
            if not journal_id:
                journal_id = self.env['account.move']._search_default_journal(journal_types=['sale'])

            accounts = self.property_id.product_tmpl_id.get_product_accounts()

            advance_account = self.env['account.account'].search([('name', '=', 'Avance recibido de clientes')], limit=1)
            # Fall back to the default income account if not found
            income_account_id = advance_account.id if advance_account else accounts['income'].id

            if not self.partial_payment_id.is_custom:
                self.env['account.move'].create({
                 'partner_id':self.tenant_id.id,
                 'auto_post': True,
                 'invoice_date':datetime.datetime.today().date(),
                 'invoice_date_due':datetime.datetime.today().date() + relativedelta(days=30),
                 'is_property_invoice': True,
                 'property_id': self.property_id.id,
                 'move_type':'out_invoice',
                 'tenancy_agreement':self.id,
                 'journal_id':journal_id.id,
                 'currency_id': self.currency_id.id,
                 'invoice_line_ids':
                         [(0, 0, {
                 'product_id':self.property_id.id,
                 'name': "Separación :" + self.property_id.name,
                 'quantity':1,
                 'price_unit': self.reserve_amount,
                 'account_id': income_account_id,
                     })]
                 })
        return
    
    def action_create_gatos_legales_invoices(self):
        if self.property_id.state == 'draft':
            raise UserError(_('This property is not confirmed yet by administrator.'))
        if self.gastos_legales_invoiced:
            raise UserError(_('Gastos Legales ya se han facturado.'))
        if self.gastos_legales <= 0:
            raise UserError(_('Gastos Legales no pueden ser cero.'))

        self.write({
            'gastos_legales_invoiced':True
            })

        journal_id = self.env['account.journal'].search([('name', 'ilike', 'no fiscal')], limit=1)
        
        if not journal_id:
            journal_id = self.env['account.move']._search_default_journal(journal_types=['sale'])
        
        accounts = self.property_id.product_tmpl_id.get_product_accounts()
        advance_account = self.env['account.account'].search([('name', '=', 'Avance recibido de clientes')], limit=1)
        # Fall back to the default income account if not found
        income_account_id = advance_account.id if advance_account else accounts['income'].id
        self.env['account.move'].create({
         'partner_id':self.tenant_id.id,
         'auto_post': True,
         'invoice_date':self.property_id.delivery_date,
         'invoice_date_due': self.property_id.delivery_date + relativedelta(days=30),
         'is_property_invoice': True,
         'property_id': self.property_id.id,
         'move_type':'out_invoice',
         'tenancy_agreement':self.id,
         'journal_id':journal_id.id,
         'currency_id': self.currency_id.id,
         'invoice_line_ids':
                 [(0, 0, {
         'product_id':self.property_id.id,
         'name': "Gastos Legales :" + self.property_id.name,
         'quantity':1,
         'price_unit': self.gastos_legales,
         'account_id': income_account_id,
             })]
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
                            'auto_post': True,
                            'invoice_date':record.agreement_start_date + relativedelta(months=record.agreement_duration),
                            'is_property_invoice': True,
                            'property_id': record.property_id.id,
                            'move_type':'out_invoice',
                            'tenancy_agreement':record.id,
                            'journal_id':journal_id.id
                            })
                        fiscal_position = inv_id.fiscal_position_id
                        accounts = record.property_id.product_tmpl_id.get_product_accounts(fiscal_pos=fiscal_position)
                        advance_account = self.env['account.account'].search([('name', '=', 'Avance recibido de clientes')], limit=1)
                        # Fall back to the default income account if not found
                        income_account_id = advance_account.id if advance_account else accounts['income'].id

                        inv_id.write({
                            'invoice_line_ids':
                        [(0, 0, {
                            'product_id':record.property_id.id,
                            'name': "Month" + str(i + 1) + ":" + record.property_id.name + "Property Rent",
                            'quantity':1,
                            'price_unit':record.property_rent,
                            'move_id':inv_id.id,
                            'account_id': income_account_id,
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
                                'account_id': income_account_id,
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
                                'account_id': income_account_id,
                                })]
                                })
                self.env['sr.property.agent.commission.lines'].create({
                    'name':self.env['ir.sequence'].next_by_code('agent.commission.line.sequence', sequence_date=fields.Datetime.context_timestamp(self, fields.Datetime.to_datetime(datetime.datetime.today().date()))),
                    'tenancy_agreement_id':record.id,
                    'date': datetime.datetime.today().date(),
                    'commission_amount':record.commission_price
                    })

    def number_to_spanish_words(self, number):
        units = ["", "uno", "dos", "tres", "cuatro", "cinco", "seis", "siete", "ocho", "nueve"]
        tens = ["", "diez", "veinte", "treinta", "cuarenta", "cincuenta", "sesenta", "setenta", "ochenta", "noventa"]
        hundreds = ["", "ciento", "doscientos", "trescientos", "cuatrocientos", "quinientos", "seiscientos", "setecientos", "ochocientos", "novecientos"]
        thousands = ["", "mil", "millón", "mil millones", "billón"]

        def spanish_number(n):
            o = n % 10
            t = (n % 100) // 10
            h = (n % 1000) // 100

            result = ""

            if n == 100:
                result = "cien"
            else:
                if t == 1 and o > 0:
                    if o == 1:
                        result = "once"
                    elif o == 2:
                        result = "doce"
                    elif o == 3:
                        result = "trece"
                    elif o == 4:
                        result = "catorce"
                    elif o == 5:
                        result = "quince"
                    else:
                        result = tens[t] + " y " + units[o]
                else:
                    result = tens[t] + ("" if t == 0 else " y ") + units[o]

                result = hundreds[h] + " " + result

            return result.strip()

        if number < 1000:
            return spanish_number(number)
        else:
            parts = []
            current = number

            for i in range(len(thousands)):
                current, rem = divmod(current, 1000)
                if rem > 0:
                    parts.append(spanish_number(rem) + " " + thousands[i])

            return ' '.join(reversed(parts)).strip()

    def price_to_words(self, amount):
        if self.property_sale_price:
            price_in_words = self.number_to_spanish_words(int(amount))
            return price_in_words.upper()
        else:
            return "El precio de venta del inmueble no está definido."

    def get_invoices_by_property(self, property_id):
        """Retrieve all unpaid invoices related to a specific property ID sorted by date."""
        invoices = self.env["account.move"].search(
            [
                ("property_id", "=", property_id),
                ("move_type", "in", ["out_invoice", "in_invoice"]),
                ("payment_state", "!=", "paid"),  # Filters out fully paid invoices
            ],
            order="invoice_date asc",
        )  # Sorts the result by invoice date in ascending order
        return invoices

    def date_to_spanish_format(self, date_obj):
        """Converts a date object to a Spanish formatted string."""
        if not date_obj:
            return ""

        # Dictionary of Spanish months
        months = {
            1: 'enero', 2: 'febrero', 3: 'marzo',
            4: 'abril', 5: 'mayo', 6: 'junio',
            7: 'julio', 8: 'agosto', 9: 'septiembre',
            10: 'octubre', 11: 'noviembre', 12: 'diciembre'
        }
        
        # Extract day, month and year from the date object
        day = date_obj.day
        month = date_obj.month
        year = date_obj.year
        year_str = str(year)
        
        # Convert day and year to their respective ordinal representations
        day_str = self._number_to_ordinal_spanish(day)
        year_suffix = year_str[2:]  # Get the last two digits of the year
        year_str = self._number_to_ordinal_spanish(int(year_suffix))
        
        # Format the string with the Spanish month and ordinal numbers
        formatted_date = f"a los {day_str} ({day}) días del mes de {months[month]} del año dos mil {year_str} (20{year_suffix})"
        return formatted_date

    def _number_to_ordinal_spanish(self, number):
        """Converts a number to its Spanish ordinal representation (text)."""
        ordinals = {
            1: 'uno', 2: 'dos', 3: 'tres', 4: 'cuatro',
            5: 'cinco', 6: 'seis', 7: 'siete', 8: 'ocho',
            9: 'nueve', 10: 'diez', 11: 'once', 12: 'doce',
            13: 'trece', 14: 'catorce', 15: 'quince', 16: 'dieciséis',
            17: 'diecisiete', 18: 'dieciocho', 19: 'diecinueve', 20: 'veinte', 21: 'veintiuno',
            22: 'veintidós', 23: 'veintitrés', 24: 'veinticuatro', 25: 'veinticinco', 26: 'veintiséis',
            27: 'veintisiete', 28: 'veintiocho', 29: 'veintinueve', 30: 'treinta', 31: 'treinta y uno',
        }
        return ordinals.get(number, str(number)) 