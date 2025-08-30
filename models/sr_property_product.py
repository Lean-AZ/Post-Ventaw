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

    property_invoice_count = fields.Integer(compute='_compute_property_invoice_count', string='Property Invoices Count')

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

    def _compute_property_invoice_count(self):
        invoice_ids = self.env["account.move"].search(
            [("property_id", "=", self.id)]
        )
        self.property_invoice_count = len(invoice_ids)

    def set_to_draft_if_no_invoices(self):
        self._compute_property_invoice_count()
        if self.property_invoice_count == 0:
            self.sudo().write({
                'state' : 'draft'
            })
        else:
            raise UserError(
                _("Cannot set to draft because there are associated invoices.")
            )

    # CRM Support
    property_leads_ids = fields.One2many(comodel_name='crm.lead', inverse_name='property_id', string='Property Leads')
    property_leads_count = fields.Integer(compute='_compute_property_leads_count', string='Property Leads Count')

    def _compute_property_leads_count(self):
        for record in self:
            record.property_leads_count = self.env['crm.lead'].search_count([('property_id', '=', record.id)])

    def action_view_property_leads_crm(self):
        self.ensure_one()
        action = self.env["ir.actions.actions"]._for_xml_id("crm.crm_case_kanban_view_leads")
        action['domain'] = [
            ('property_id', '=', self.id)
        ]
        return action
    # End CRM Support
    

class srPropertytemplate(models.Model):
    _inherit = 'product.template'

    @api.model
    def default_get(self, fields):
        res = super(srPropertytemplate, self).default_get(fields)
        if 'company_id' in fields:
            res['company_id'] = self.env.company.id
        return res

    @api.onchange('property_type')
    def onchage_property_type(self):
        if self.property_type == 'sale':
            self.property_maintenance_interval_type = 'one_time'
        return


    # CRM Support
    property_leads_ids = fields.One2many(comodel_name='crm.lead', inverse_name='property_id', string='Property Leads')
    property_leads_count = fields.Integer(compute='_compute_property_leads_count', string='Property Leads Count')

    def _compute_property_leads_count(self):
        for record in self:
            record.property_leads_count = self.env['crm.lead'].search_count([('property_id', '=', record.id)])

    def action_view_property_leads_crm(self):
        self.ensure_one()
        action = self.env["ir.actions.actions"]._for_xml_id("crm.crm_case_kanban_view_leads")
        action['domain'] = [
            ('property_id', '=', self.id)
        ]
        return action
    # End CRM Support


    is_property = fields.Boolean('Is Property?')
    property_type = fields.Selection([('sale', 'Sale'), ('rent', 'Rent')], string="Property For", default="sale")
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
    cadastral_designation = fields.Char("Designación Catastral")
    cadastral_number = fields.Char("Número Catastral")
    property_carpet_area = fields.Float('Carpet Area', default=1)
    property_build_up_area = fields.Float('Build-up Area', default=1)
    property_floor = fields.Integer('Floor', default=1)
    property_badrooms = fields.Integer('Badrooms', default=1)
    property_bathrooms = fields.Integer("Baños", default=1)
    property_parking_lots = fields.Integer("Parqueos", default=0)
    property_bloque = fields.Char("Bloque")
    property_building_number = fields.Char("Edificio")
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
    state = fields.Selection(
        [
            ("draft", "Draft"),
            ("available", "Available"),
            ("booked", "Separado"),
            ("rented", "Rented"),
            ("sold", "Sold"),
        ],
        string="Status",
        readonly=True,
        copy=False,
        index=True,
        track_visibility="onchange",
    )
    property_invoice_count = fields.Integer(compute='_compute_property_invoice_count', string='Property Invoices Count')
    tenancy_agreement_count = fields.Integer(compute='_compute_tenancy_agreement_count', string='Tenancy Agreement Count')
    current_user_id = fields.Many2one('res.partner','Current User')
    reservation_history_ids = fields.Many2many('res.partner',string="Reservation history")
    currency_id = fields.Many2one(
        "res.currency",
        string="Moneda",
        readonly=False,
        domain="[('active', '=', True)]",
        store=True,
    )
    delivery_date = fields.Date("Fecha de entrega", store=True)

    percentage_paid = fields.Float(
        string="Porcentaje Pagado",
        compute="_compute_percentage_paid",
    )

    all_invoice_lines = fields.One2many(
        "account.move.line",
        string="All Invoice Lines",
        compute="_compute_all_invoice_lines",
        store=False,
    )

    all_cuotas = fields.One2many(
        "account.move.line",
        string="All Cuotas",
        compute="_compute_all_invoice_lines",
        store=False,
    )

    total_cuotas = fields.Float(
        string="Total Cuotas",
        compute="_compute_all_invoice_lines",
        store=False,
    )

    all_mora_lines = fields.One2many(
        "account.move.line",
        string="All Mora Lines",
        compute="_compute_all_invoice_lines",
        store=False,
    )

    all_cuota_final_lines = fields.One2many(
        "account.move.line",
        string="All Cuota Final Lines",
        compute="_compute_all_invoice_lines",
        store=False,
    )

    total_cuota_final = fields.Float(
        string="Total Cuota Final",
        compute="_compute_all_invoice_lines",
        store=False,
    )

    total_mora = fields.Float(
        string="Total Mora",
        compute="_compute_all_invoice_lines",
        store=False,
    )

    all_ajustes = fields.One2many(
        "account.move.line",
        string="All Ajustes",
        compute="_compute_all_invoice_lines",
        store=False,
    )
    total_ajustes = fields.Float(
        string="Total Ajustes",
        compute="_compute_all_invoice_lines",
        store=False,
    )

    all_cuotas_addon = fields.One2many(
        "account.move.line",
        string="Extras",
        compute="_compute_all_invoice_lines",
        store=False,
    )

    total_cuotas_addon = fields.Float(
        string="Total Extras",
        compute="_compute_all_invoice_lines",
        store=False,
    )

    total_cuotas_addon_debt = fields.Float(
        string="Total Extras Pendientes",
        compute="_compute_all_invoice_lines",
        store=False,
    )

    total_paid_subtotal = fields.Float(
        string="Total Capital Pagado", compute="_compute_all_invoices", store=False
    )

    total_partial_paid_subtotal = fields.Float(
        string="Total Cuotas Parcialmente Pagadas",
        compute="_compute_all_invoice_lines",
        store=False,
    )

    total_paid_mora = fields.Float(
        string="Total Mora Pagada", compute="_compute_all_invoices", store=False
    )

    total_paid_ajustes = fields.Float(
        string="Total Paid Ajustes", compute="_compute_all_invoice_lines", store=False
    )

    total_paid_cuota_final = fields.Float(
        string="Total Paid Cuota Final",
        compute="_compute_all_invoice_lines",
        store=False,
    )

    all_gastos_legales_lines = fields.One2many(
        "account.move.line",
        string="All Gastos Legales Lines",
        compute="_compute_all_invoice_lines",
        store=False,
    )

    total_gastos_legales = fields.Float(
        string="Total Gastos Legales",
        compute="_compute_all_invoice_lines",
        store=False,
    )

    all_gastos_legales_paid_lines = fields.One2many(
        "account.move.line",
        string="All Gastos Legales Paid Lines",
        compute="_compute_all_invoice_lines",
        store=False,
    )

    def _compute_all_invoices(self):
        for record in self:
            all_invoices = self.env["account.move"].search(
                [("property_id.product_tmpl_id", "=", record.id)]
            )
            record.total_paid_mora = sum(all_invoices.mapped("mora_pagada_custom_sr"))
            record.total_paid_subtotal = sum(all_invoices.mapped("capital_pagado_custom_sr"))

    def _compute_all_invoice_lines(self):
        for record in self:
            # Fetch all lines related to this product template
            all_lines = self.env["account.move.line"].search(
                [("move_id.property_id.product_tmpl_id", "=", record.id)]
            )

            # Sort all_lines by move_id.invoice_date (ascending)
            all_lines = all_lines.sorted(
                key=lambda l: l.move_id.invoice_date, reverse=False
            )

            # Group lines dynamically based on the description
            cuotas_lines = all_lines.filtered(
                lambda l: l.name
                and any(
                    word in l.name.lower()
                    for word in ["cuota", "reserva", "separación", "aumento"]
                )
                and "final" not in l.name.lower()
            )

            cuota_final_lines = all_lines.filtered(
                lambda l: l.name and "final" in l.name.lower()
            )

            mora_lines = all_lines.filtered(
                lambda l: l.name and "mora" in l.name.lower()
            )
            ajustes_lines = all_lines.filtered(
                lambda l: l.name
                and any(word in l.name.lower() for word in ["ajuste", "aumento"])
            )
            # Filter only lines from PAID invoices
            paid_invoice_lines = cuotas_lines.filtered(
                lambda l: l.move_id.payment_state == "paid"
            )
            partial_paid_invoice_lines = cuotas_lines.filtered(
                lambda l: l.move_id.payment_state == "partial"
            )

            paid_ajustes_lines = ajustes_lines.filtered(
                lambda l: l.move_id.payment_state == "paid"
            )

            paid_cuota_final_lines = cuota_final_lines.filtered(
                lambda l: l.move_id.payment_state in ["paid", "partial"]
            )

            first_paid_cuota_final_line = (
                paid_cuota_final_lines[0] if paid_cuota_final_lines else None
            )

            # Filter gastos legales lines
            gastos_legales_lines = all_lines.filtered(
                lambda l: l.name and "legales" in l.name.lower()
            )

            # Filter gastos legales lines from paid invoices
            gastos_legales_paid_lines = gastos_legales_lines.filtered(
                lambda l: l.move_id.payment_state == "paid"
            )

            cuotas_addon_lines = all_lines.filtered(
                lambda l: l.move_id.is_property_addon and l.price_subtotal > 0
            )

            debt_cuotas_addon_lines = cuotas_addon_lines.filtered(
                lambda l: l.move_id.payment_state != "paid"
            )

            total_cuotas_addon_debt = sum(
                debt_cuotas_addon_lines.mapped("move_id.amount_residual")
            )

            # Assign the filtered groups to respective fields
            record.all_invoice_lines = all_lines
            record.all_cuotas = cuotas_lines
            record.all_cuotas_addon = cuotas_addon_lines
            record.total_cuotas_addon = sum(cuotas_addon_lines.mapped("price_subtotal"))
            record.total_cuotas_addon_debt = total_cuotas_addon_debt
            record.total_cuotas = sum(cuotas_lines.mapped("price_subtotal"))
            record.total_partial_paid_subtotal = (
                sum(partial_paid_invoice_lines.mapped("move_id.amount_total"))
                - sum(partial_paid_invoice_lines.mapped("move_id.amount_residual"))
                + sum(paid_invoice_lines.mapped("price_subtotal"))
            )
            record.all_mora_lines = mora_lines
            record.total_mora = sum(mora_lines.mapped("price_subtotal"))
            record.all_ajustes = ajustes_lines
            record.total_ajustes = sum(ajustes_lines.mapped("price_subtotal"))
            record.all_cuota_final_lines = cuota_final_lines
            record.total_cuota_final = sum(cuota_final_lines.mapped("price_subtotal"))
            record.all_gastos_legales_lines = gastos_legales_lines
            record.total_gastos_legales = sum(
                gastos_legales_lines.mapped("price_subtotal")
            )

            # New field: Sum of all ajustes lines where the invoice is paid
            record.total_paid_ajustes = sum(paid_ajustes_lines.mapped("price_subtotal"))

            # New field: Sum of all cuota final lines where the invoice is paid
            # record.total_paid_cuota_final = sum(paid_cuota_final_lines.mapped('price_subtotal'))
            record.total_paid_cuota_final = (
                first_paid_cuota_final_line.move_id.amount_total
                - first_paid_cuota_final_line.move_id.amount_residual
                if first_paid_cuota_final_line
                else 0.0
            )

    @api.depends(
        "total_paid_subtotal",
        "total_paid_ajustes",
        "total_cuota_final",
        "property_sale_price",
        "total_ajustes",
    )
    def _compute_percentage_paid(self):
        for record in self:

            total_paid = (record.total_paid_subtotal or 0.0) + (
                record.total_paid_cuota_final or 0.0
            )

            # Total expected amounts
            total_sale_amount = record.property_sale_price or 0.0

            # Calculate percentage paid
            if total_sale_amount > 0:
                record.percentage_paid = (total_paid / total_sale_amount) * 100
            else:
                record.percentage_paid = 0.0

    invoices_ids = fields.Many2many(
        "account.move",
        string="Invoices",
        compute="_compute_invoices_ids",
        store=False,
    )
    grouped_invoices = fields.One2many(
        "account.move",
        string="Grouped Invoices",
        compute="_compute_grouped_invoices",
        store=False,
    )

    monto_reserva_invoices = fields.One2many(
        "account.move",
        string="Monto Reserva Invoices",
        compute="_compute_monto_reserva_invoices",
        store=False,
    )

    first_tenancy_agreement_id = fields.Many2one(
        "sr.tenancy.agreement",
        string="First Tenancy Agreement",
        compute="_compute_tenancy_agreement_count",
        store=False,
    )

    def _compute_grouped_invoices(self):
        InvoiceGroup = namedtuple(
            "InvoiceGroup",
            ["invoice_date", "amount_total", "amount_residual", "payment_state"],
        )
        for record in self:
            # Initialize sum variables
            total_amount = 0
            residual_amount = 0

            # Find all relevant invoices
            invoices = self.env["account.move"].search(
                [
                    ("move_type", "in", ["out_invoice", "out_refund"]),
                    ("property_id.product_tmpl_id", "=", record.id),
                ]
            )

            # Filter and sum the invoices based on the description
            for invoice in invoices:
                for line in invoice.invoice_line_ids:
                    if "Inicial Cuota" in line.name:
                        total_amount += invoice.amount_total
                        residual_amount += invoice.amount_residual

            grouped_invoice = InvoiceGroup(
                invoice_date=fields.Date.context_today(self),
                amount_total=total_amount,
                amount_residual=residual_amount,
                payment_state="N/A",
            )

            record.grouped_invoices = [grouped_invoice]

    def _compute_monto_reserva_invoices(self):
        InvoiceGroup = namedtuple(
            "InvoiceGroup",
            ["invoice_date", "amount_total", "amount_residual", "payment_state"],
        )
        for record in self:
            # Initialize sum variables
            total_amount = 0
            residual_amount = 0

            # Find all relevant invoices
            invoices = self.env["account.move"].search(
                [
                    ("move_type", "in", ["out_invoice", "out_refund"]),
                    ("property_id.product_tmpl_id", "=", record.id),
                ]
            )

            # Filter and sum the invoices based on the description
            for invoice in invoices:
                for line in invoice.invoice_line_ids:
                    if "Monto de reserva" in line.name:
                        total_amount += invoice.amount_total
                        residual_amount += invoice.amount_residual

            # Create a single "dummy" invoice-like object to hold the aggregated values
            grouped_invoice = InvoiceGroup(
                invoice_date=fields.Date.context_today(self),
                amount_total=total_amount,
                amount_residual=residual_amount,
                payment_state="N/A",  # Custom payment state, or summarize the state if needed
            )

            record.monto_reserva_invoices = [grouped_invoice]

    def _compute_invoices_ids(self):
        for record in self:
            invoices = self.env["account.move"].search(
                [
                    ("move_type", "in", ["out_invoice", "out_refund"]),
                    ("property_id.product_tmpl_id", "=", record.id),
                ]
            )
            record.invoices_ids = invoices

    def action_view_tenancy_agreement(self):
        self.ensure_one()
        action = self.env["ir.actions.actions"]._for_xml_id(
            "sr_property_rental_management.sr_property_tenancy_agreement_action"
        )
        action["domain"] = [
            ("property_id.product_tmpl_id", "=", self.id),
        ]
        return action

    def action_view_property_invoices(self):
        self.ensure_one()
        action = self.env["ir.actions.actions"]._for_xml_id(
            "account.action_move_out_invoice_type"
        )
        action["domain"] = [
            ("move_type", "in", ("out_invoice", "out_refund")),
            ("property_id", "=", self.id),
        ]
        action["context"] = {
            "default_move_type": "out_invoice",
            "move_type": "out_invoice",
            "journal_type": "sale",
            "search_default_unpaid": 1,
        }
        return action

    def _compute_tenancy_agreement_count(self):
        for record in self:
            agreement_ids = self.env["sr.tenancy.agreement"].search(
                [("property_id.product_tmpl_id", "=", record.id)]
            )
            record.tenancy_agreement_count = len(agreement_ids)
            record.first_tenancy_agreement_id = (
                agreement_ids[:1] if agreement_ids else False
            )

    def _compute_property_invoice_count(self):
        invoice_ids = self.env["account.move"].search(
            [("property_id.product_tmpl_id", "=", self.id)]
        )
        self.property_invoice_count = len(invoice_ids)

    def action_confirm(self):
        if self.property_type == "sale":
            if self.property_sale_price <= 0:
                raise UserError(_("Please enter reasonable property sale price"))
        if self.property_type == "rent":
            if self.property_rent_price <= 0:
                raise UserError(_("Please enter reasonable property rent price"))
        self.sudo().write(
            {
                "state": "available",
            }
        )
        return


    def set_to_draft_if_no_invoices(self):
        self._compute_property_invoice_count()
        if self.property_invoice_count == 0:
            self.sudo().write({
                'state' : 'draft'
            })
        else:
            raise UserError(
                _("Cannot set to draft because there are associated invoices.")
            )

class AccountMove(models.Model):
    _inherit = "account.move"

    is_overdue = fields.Boolean(compute="_compute_is_overdue")

    property_amount_paid = fields.Float(
        string="Monto Pagado",
        default=0.00
    )

    paid_mora = fields.Float(
        string="Mora Pagada",
        default=0.00
    )

    paid_capital = fields.Float(
        string="Capital Pagado",
        default=0.00
    )

    def get_report_data(self):
        # Assuming 'self' is a single record of account.move
        # Prepare required data
        from_currency = self.currency_id
        to_currency = self.env.user.company_id.currency_id
        company = self.company_id
        date = self.invoice_date or fields.Date.today()

        Currency = self.env["res.currency"]
        dop_currency = Currency.search([("name", "=", "DOP")], limit=1)
        if not dop_currency:
            raise UserError(_("Currency DOP not found."))
        # Calculate conversion rate
        conversion_rate = self.env["res.currency"]._get_conversion_rate(
            from_currency, to_currency, company, date
        )

        payments = self.env["account.payment"].search(
            [("reconciled_invoice_ids", "in", self.ids)]
        )
        payment_date = payments[0].date if payments else None

        return {
            "conversion_rate": conversion_rate,
            "from_currency": from_currency.name,
            "to_currency": to_currency.name,
            "company_name": company.name,
            "date": payment_date,
            # Include other data as needed for the report
        }


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
    
