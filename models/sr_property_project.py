from odoo import models, fields, api, _

class srPropertyProject(models.Model):
    _name = 'sr.property.project'
    _description = 'Property Project'

    name = fields.Char('Name')
    description = fields.Text('Description')
    number_of_units = fields.Integer('Number of Units', compute='_compute_number_of_units')
    interest_percent = fields.Float('Interest Percent')
    days_to_compute = fields.Integer('Days to Compute')

    property_id = fields.One2many('product.product', 'sr_property_project_id', string='Properties', domain="[('is_property','=', True)]")

    @api.depends('property_id')
    def _compute_number_of_units(self):
        for record in self:
            record.number_of_units = len(record.property_id)