from odoo import models, fields, api,  _
from odoo.exceptions import UserError

class srPropertyLead(models.Model):
    _inherit = 'crm.lead'

    is_property_lead = fields.Boolean('Is Property Lead?', default=False)
    property_id = fields.Many2one('product.product', string='Property', domain="[('is_property','=', True)]")