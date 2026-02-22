from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
import datetime
from dateutil.relativedelta import relativedelta


class srPropertyAgentCommissionSettlementLines(models.Model):
    _name = "sr.property.agent.commission.settlement.lines"

    property_id = fields.Many2one("product.product", string="Property")
    tenancy_agreement_id = fields.Many2one(
        "sr.tenancy.agreement", string="Tenancy Agreement"
    )
    date = fields.Date(
        string="Date", required=True, copy=False, default=fields.Datetime.now
    )
    currency_id = fields.Many2one("res.currency", string="Currency")
    commission_amount = fields.Float("Commission", currency_field="currency_id")
    commission_settlement_id = fields.Many2one(
        "sr.property.agent.commission.settlement", string="Commission Settlement"
    )
    commission_line = fields.Many2one(
        "sr.property.agent.commission.lines", string="Commission Line Reference"
    )


class srPropertyAgentCommissionSettlement(models.Model):
    _name = "sr.property.agent.commission.settlement"

    name = fields.Char(
        string="Commission Settlement Reference",
        required=True,
        copy=False,
        readonly=True,
        index=True,
        default=lambda self: _("New"),
    )
    date = fields.Date(
        string="Date", required=True, copy=False, default=fields.Datetime.now
    )
    agent_commission_line_ids = fields.One2many(
        "sr.property.agent.commission.settlement.lines",
        "commission_settlement_id",
        string="Commission Settlement Lines",
    )
    agent_id = fields.Many2one("res.partner", "agent", required=True)
    commission_structure_id = fields.Many2one(
        "sr.agent.commission.structure", "Estructura de Comisión", required=True
    )
    state = fields.Selection(
        [
            ("new", "New"),
            ("confirm", "Confirmed"),
            ("invoiced", "Invoiced"),
        ],
        string="Status",
        readonly=True,
        copy=False,
        index=True,
        tracking=True,
        default="new",
    )

    def calculate_agent_commission(self):
        self.agent_commission_line_ids.unlink()
        comm_line = self.env["sr.property.agent.commission.lines"].search(
            [
                ("commission_structure_id", "=", self.commission_structure_id.id),
                ("is_commission_settled", "=", False),
            ]
        )
        print("====comm_line", comm_line)
        for line in comm_line:
            self.write(
                {
                    "agent_commission_line_ids": [
                        (
                            0,
                            0,
                            {
                                "property_id": line.property_id.id,
                                "tenancy_agreement_id": line.tenancy_agreement_id.id,
                                "date": line.date,
                                "currency_id": line.currency_id.id,
                                "commission_amount": line.commission_amount,
                                "commission_line": line.id,
                            },
                        )
                    ]
                }
            )
        return

    def action_confirm(self):
        if not self.agent_commission_line_ids:
            raise UserError(
                _(
                    "There is no any commission Lines.\n Please Calculate commission line or contact your administrator"
                )
            )
        for record in self.agent_commission_line_ids:
            record.commission_line.write(
                {"is_commission_settled": True, "commission_settlement_id": self.id}
            )
        self.write(
            {
                "name": self.env["ir.sequence"].next_by_code(
                    "agent.commission.settlement.sequence",
                    sequence_date=fields.Datetime.context_timestamp(
                        self,
                        fields.Datetime.to_datetime(datetime.datetime.today().date()),
                    ),
                ),
                "state": "confirm",
            }
        )

    def action_create_invoice(self):
        journal_id = self.env["account.move"]._search_default_journal(
            journal_types=["purchase"]
        )
        inv_id = self.env["account.move"].create(
            {
                "partner_id": self.agent_id.id,
                "invoice_date": datetime.datetime.today().date(),
                "is_property_commission_bill": True,
                "move_type": "in_invoice",
                "journal_id": journal_id.id,
            }
        )
        for record in self.agent_commission_line_ids:
            fiscal_position = inv_id.fiscal_position_id
            accounts = record.property_id.product_tmpl_id.get_product_accounts(
                fiscal_pos=fiscal_position
            )
            inv_id.write(
                {
                    "invoice_line_ids": [
                        (
                            0,
                            0,
                            {
                                "product_id": record.property_id.id,
                                "name": record.property_id.name
                                + "Comision. Contrato No:"
                                + str(record.tenancy_agreement_id.name),
                                "quantity": 1,
                                "price_unit": record.commission_amount,
                                "account_id": accounts["income"].id,
                                "tenancy_agreement": record.tenancy_agreement_id.id,
                            },
                        )
                    ]
                }
            )
        self.state = "invoiced"
        return



class srPropertyCommissionWizzardInvoice(models.TransientModel):
    _name = "sr.property.commission.wizzard.invoice"
    
    property_id = fields.Many2one("product.product", string="Propiedad")
    commission_structure_id = fields.Many2one("sr.agent.commission.structure", string="Estructura de Comisión")
    date = fields.Date(string="Fecha")
    commission_amount = fields.Monetary(string="Monto de Comisión")
    currency_id = fields.Many2one("res.currency", string="Moneda")
    invoice_type = fields.Selection([("percentage", "Porcentaje"),("all", "Todo")], string="Tipo de Factura", default="all")
    percetage_to_pay = fields.Float(string="Porcentaje a Pagar")
    fixed_amount_to_pay = fields.Float(string="Monto Fijo a Pagar")
    commission_line_id = fields.Many2one("sr.property.agent.commission.lines", string="Linea de Comisión")
    tenancy_agreement_id = fields.Many2one("sr.tenancy.agreement", string="Contrato")
    journal_id = fields.Many2one("account.journal", string="Diario")

    @api.model
    def default_get(self, fields):
        result = super(srPropertyCommissionWizzardInvoice, self).default_get(fields)
        if self._context.get("active_id"):
            commission_line = self.env["sr.property.agent.commission.lines"].browse(
                [self._context.get("active_id")]
            )
            result["commission_amount"] = commission_line.remaining_amount
            result["date"] = commission_line.date
            result["currency_id"] = commission_line.currency_id.id
            result["commission_line_id"] = commission_line.id
            result["commission_structure_id"] = commission_line.commission_structure_id.id
            result["property_id"] = commission_line.property_id.id
            result["tenancy_agreement_id"] = commission_line.tenancy_agreement_id.id

        return result

    def generate_commission_invoices(self):
        # journal_id = self.env["account.move"]._search_default_journal(
        #     journal_types=["purchase"]
        # )

        for line in self.commission_structure_id.agent_commission_structure_lines_ids:
            amount_to_pay = 0
            if self.invoice_type == "percentage":
                amount_to_pay = (self.commission_amount * self.percetage_to_pay / 100) * line.percentage / 100
            elif self.invoice_type == "all":
                amount_to_pay = self.commission_amount * line.percentage / 100

            self.env['account.move'].create({
                'partner_id': line.agent_id.id,
                'invoice_date': datetime.datetime.today().date(),
                'is_property_commission_bill': True,
                'property_id': self.property_id.id,
                'move_type': 'in_invoice',
                'journal_id': self.journal_id.id,
                'currency_id': self.currency_id.id,
                'commission_line_id': self.commission_line_id.id,
                'invoice_line_ids': [
                    (0, 0, {
                        'name': self.property_id.name + " Comision. Contrato No:" + str(self.tenancy_agreement_id.name),
                        'quantity': 1,
                        'price_unit': amount_to_pay,
                    })
                ]
            })
        return


class srPropertyAgentCommissionLines(models.Model):
    _name = "sr.property.agent.commission.lines"

    name = fields.Char(
        string="Commission Line Reference",
        required=True,
        copy=False,
        readonly=True,
        index=True,
        default=lambda self: _("New"),
    )
    property_id = fields.Many2one(
        "product.product",
        "Property",
        required=True,
        related="tenancy_agreement_id.property_id",
    )
    tenancy_agreement_id = fields.Many2one(
        "sr.tenancy.agreement", "Agreement", required=True
    )
    date = fields.Date(
        string="Date", required=True, copy=False, default=fields.Datetime.now
    )
    agent_id = fields.Many2one(
        "res.partner",
        required=True,
        copy=False,
        related="tenancy_agreement_id.agent_id",
    )
    commission_type = fields.Selection(
        [("fixed", "Fixed"), ("percentage", "Percentage")],
        string="Commission Type",
        related="tenancy_agreement_id.commission_type",
    )
    commission_amount = fields.Float("Commission", currency_field="currency_id")
    invoiced_amount = fields.Float("Monto Facturado", currency_field="currency_id", compute="_compute_invoiced_amount")
    paid_amount = fields.Float("Monto Pagado", currency_field="currency_id", compute="_compute_paid_amount")
    remaining_amount = fields.Float("Monto Pendiente", currency_field="currency_id", compute="_compute_remaining_amount")

    currency_id = fields.Many2one(
        "res.currency", string="Currency", related="tenancy_agreement_id.currency_id"
    )
    is_commission_settled = fields.Boolean("Is Commission Settled?")
    commission_settlement_id = fields.Many2one(
        "sr.property.agent.commission.settlement", string="Commission Settlement"
    )
    commission_structure_id = fields.Many2one(
        "sr.agent.commission.structure",
        string="Estructura de Comisión",
        related="tenancy_agreement_id.commission_structure_id",
    )
    invoiceable_line_ids = fields.One2many(
        "sr.property.agent.commission.invoiceable.lines",
        "commission_line_id",
        string="Invoiceable Lines",
    )
    linked_invoices_ids = fields.One2many(
        "account.move", "commission_line_id", string="Linked Invoices"
    )
    linked_invoice_count = fields.Integer(
        string="Linked Invoices Count", compute="_compute_linked_invoice_count"
    )
    state = fields.Selection(
        [
            ("draft", "Borrador"),
            ("partially_invoiced", "Parcialmente Facturado"),
            ("invoiced", "Facturado"),
        ],
        string="Estado",
        default="draft",
    )

    project = fields.Many2one("sr.property.project", string="Proyecto", compute="_compute_project_from_property")
    property_sale_price = fields.Float(string="Precio de Venta", compute="_compute_property_sale_price")
    property_status = fields.Selection(
        [
            ("draft", "Borrador"),
            ("available", "Disponible"),
            ("booked", "Separado"),
            ("rented", "Alquilado"),
            ("sold", "Vendido"),
        ],
        string="Estado de la Propiedad", compute="_compute_property_status")
    property_client_id = fields.Many2one("res.partner", string="Cliente", compute="_compute_property_client_id")

    commission_percetage = fields.Float(string="Porcentaje de Comisión", compute="_compute_commission_percentage")

    @api.depends("commission_structure_id")
    def _compute_commission_percentage(self):
        for record in self:
            record.commission_percetage = record.commission_structure_id.percentage

    @api.depends("tenancy_agreement_id")
    def _compute_property_client_id(self):
        for record in self:
            record.property_client_id = record.tenancy_agreement_id.tenant_id
    
    @api.depends("property_id")
    def _compute_property_status(self):
        for record in self:
            record.property_status = record.property_id.state

    @api.depends("tenancy_agreement_id")
    def _compute_property_sale_price(self):
        for record in self:
            record.property_sale_price = record.tenancy_agreement_id.property_sale_price

    @api.depends("property_id")
    def _compute_project_from_property(self):
        for record in self:
            record.project = record.property_id.sr_property_project_id


    @api.depends("linked_invoices_ids")
    def _compute_invoiced_amount(self):
        for record in self:
            record.invoiced_amount = sum(record.linked_invoices_ids.mapped("amount_total_in_currency_signed"))
    
    @api.depends("linked_invoices_ids")
    def _compute_paid_amount(self):
        for record in self:
            record.paid_amount = sum(record.linked_invoices_ids.mapped("amount_total")) - sum(record.linked_invoices_ids.mapped("amount_residual"))
    
    @api.depends("linked_invoices_ids")
    def _compute_remaining_amount(self):
        for record in self:
            record.remaining_amount = record.commission_amount - record.paid_amount
            if record.remaining_amount == record.commission_amount:
                record.state = "draft"
            if record.remaining_amount < record.commission_amount:
                record.state = "partially_invoiced"
            if record.remaining_amount == 0:
                record.state = "invoiced"
            if record.remaining_amount < 0:
                record.remaining_amount = 0

    @api.depends("linked_invoices_ids")
    def _compute_linked_invoice_count(self):
        for record in self:
            record.linked_invoice_count = len(record.linked_invoices_ids)

    def action_view_linked_invoices(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": "Linked Invoices",
            "res_model": "account.move",
            "view_mode": "tree,form",
            "domain": [("commission_line_id", "=", self.id)],
        }


class srPropertyAgentCommissionInvoiceableLines(models.Model):
    _name = "sr.property.agent.commission.invoiceable.lines"

    name = fields.Char(
        string="Invoiceable Line Reference",
        required=True,
        copy=False,
        readonly=True,
        index=True,
        default=lambda self: _("New"),
    )
    property_id = fields.Many2one(
        "product.product",
        "Property",
        required=True,
        related="tenancy_agreement_id.property_id",
    )
    tenancy_agreement_id = fields.Many2one(
        "sr.tenancy.agreement", "Agreement", required=True
    )
    date = fields.Date(
        string="Date", required=True, copy=False, default=fields.Datetime.now
    )
    agent_id = fields.Many2one("res.partner", string="Agente")
    currency_id = fields.Many2one(
        "res.currency", string="Currency", related="property_id.currency_id"
    )
    amount = fields.Monetary(string="Monto", currency_field="currency_id")
    commission_line_id = fields.Many2one(
        "sr.property.agent.commission.lines", string="Commission Line"
    )
