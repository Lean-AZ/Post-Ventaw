from odoo import models, fields, api


class PropertyUnit(models.Model):
    _name = 'property.unit'

    name = fields.Char(string='Unit')
    unit_type = fields.Selection([('sale', 'Sale'), ('rent', 'Rent')], string="Unit     For", default="rent")
    unit_rent_price = fields.Float(
        'Unit Rent Price', default=1.0,
        digits='Unit Price',
        help="Price at which the Unit is Rented to Tenants.")
    unit_construction_status = fields.Selection([('under_const', 'Under Construction'), ('ready_to_move', 'Ready To Move')], string="Unit Status", default="ready_to_move")
    user_id = fields.Many2one('res.users', string="Sales Person", default=lambda self: self.env.user)
    unit_carpet_area = fields.Float('Carpet Area', default=1)
    unit_build_up_area = fields.Float('Build-up Area', default=1)
    unit_floor = fields.Integer('Floor', default=1)
    unit_badrooms = fields.Integer('Badrooms', default=1)
    unit_balconies = fields.Float('Balconies', default=1)
    unit_maintenance_charge = fields.Float('Maintenance Charge', default=1)
    unit_gas_safety_exp_date = fields.Date('Gas Safety Expiry Date')
    unit_gas_safety_exp_attch = fields.Binary('Gas Safety Expiry Attachment')
    electricity_safety_certificate = fields.Binary('Electricity Safety Certificate Attachment')
    epc = fields.Char('Energy Performance (EPC)')
    address = fields.Char(string='Address')
    unit_maintenance_interval_type = fields.Selection([('month', 'Monthly'), ('year', 'Yearly'), ('one_time', 'One Time')], string="Maintenance Interval ", default="month")


    @api.onchange('unit_type')
    def onchage_property_type(self):
        if self.unit_type == 'sale':
            self.unit_maintenance_interval_type = 'one_time'
        return


    image_1920 = fields.Image("Image", max_width=1920, max_height=1920)

class ProductUnit(models.Model):
    _inherit = 'product.product'

    unite_id = fields.One2many('unit.unit','property_id')


class Unit(models.Model):
    _name = 'unit.unit'

    property_id = fields.Many2one('product.product')
    name_unit = fields.Many2one('property.unit', string='Unit Name')
    rate = fields.Float(string='Rate')
    carpet_area = fields.Float(string='Area')
    maintenance_charge = fields.Float(string='Maintenance Charge')
    address = fields.Char(string='Address')

    @api.onchange('name_unit')
    def onchange_method(self):
        for rec in self:
            rec.rate = rec.name_unit.unit_rent_price
            rec.carpet_area = rec.name_unit.unit_carpet_area
            rec.maintenance_charge = rec.name_unit.unit_maintenance_charge
            rec.address = rec.name_unit.address
