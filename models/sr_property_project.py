from odoo import models, fields, api, _
from odoo.exceptions import UserError

class srPropertyProject(models.Model):
    _name = 'sr.property.project'
    _description = 'Proyecto Inmobiliario'
    _inherit = ['mail.thread', 'mail.activity.mixin']   # Permite chatter y actividades

    name = fields.Char('Name')
    description = fields.Text('Description')
    number_of_units = fields.Integer('Cantidad de Unidades', compute='_compute_number_of_units')
    interest_percent = fields.Float('Porcentaje de Interés (mora)')
    days_to_compute = fields.Integer('Días de gracia (mora)')

    property_id = fields.One2many('product.product', 'sr_property_project_id', string='Propiedades', domain="[('is_property','=', True)]")

    @api.depends('property_id')
    def _compute_number_of_units(self):
        for record in self:
            record.number_of_units = len(record.property_id)


    # ghr units integration

    code = fields.Char('Code')
    default_inspector_id = fields.Many2one('res.users', string='Inspector Predeterminado')
    default_technician_id = fields.Many2one('res.users', string='Técnico Predeterminado')

 # MODELO: Categoría personalizada para tickets inmobiliarios
class HelpdeskTicketCategory(models.Model):
    _name = 'helpdesk.ticket.category'
    _description = 'Categoría GHR'
    
    name = fields.Char(string='Nombre', required=True)
    active = fields.Boolean(default=True)

class HelpdeskTicketQuestion(models.Model):
    _name = 'helpdesk.ticket.question'
    _description = 'Problema Específico'
    
    name = fields.Char(string='Pregunta/Problema', required=True)
    active = fields.Boolean(default=True)
    category_id = fields.Many2one('helpdesk.ticket.category', string='Categoría', ondelete='cascade', required=True)
# HERENCIA DEL MODELO helpdesk.ticket
class HelpdeskTicket(models.Model):
    _inherit = 'helpdesk.ticket'

    radicado = fields.Char(string='Radicado GHR', readonly=True, default='/')

    # Unidad inmobiliaria asociada al ticket
    unit_id = fields.Many2one('product.product', string='Unidad Inmobiliaria', domain=[('is_property', '=', True)], required=True)
     # Proyecto relacionado automáticamente desde la unidad
    unit_project_id = fields.Many2one('sr.property.project', related='unit_id.product_tmpl_id.sr_property_project_id', string='Proyecto Inmobiliario', store=True, readonly=True)
      # Categoría personalizada
    category_inm_id = fields.Many2one('helpdesk.ticket.category', string='Categoría Inmobiliaria')
     # Problema específico relacionado a la categoría seleccionada
    question_inm_id = fields.Many2one('helpdesk.ticket.question', string='Problema Específico')
    ticket_photos = fields.Many2many('ir.attachment', string='Fotos del Hallazgo')
       # Día preferido de visita
    preferred_visit_days = fields.Selection([
        ('lunes', 'Lunes'), ('martes', 'Martes'), ('miercoles', 'Miércoles'),
        ('jueves', 'Jueves'), ('viernes', 'Viernes'), ('sabado', 'Sábado')
    ], string='Días Preferidos')
      # Horario preferido de visita
    preferred_time_slot = fields.Selection([
        ('am', '08:00 AM - 12:00 PM'), ('pm_early', '02:00 PM - 04:00 PM'), ('pm_late', '04:00 PM - 06:00 PM')
    ], string='Horario Preferido')
      # Inspector asignado
    inspector_id = fields.Many2one('res.users', string='Inspector Asignado')
        # Técnico asignado
    technician_id = fields.Many2one('res.users', string='Técnico Asignado')
     # Firma digital del cliente (campo binario tipo imagen)
    signature_client = fields.Binary(string='Firma del Cliente')
       # Firma del ingeniero (campo binario tipo imagen)
    signature_engineer = fields.Binary(string='Firma del Ingeniero')
      # Indica si la unidad está en garantía
    warranty_status = fields.Boolean(related='unit_id.product_tmpl_id.warranty_status', string="En Garantía")

    # --- ONCHANGES ---
    @api.onchange('partner_id')
    def _onchange_partner_id_clear_unit(self):
        if self.partner_id:
            self.unit_id = False

    @api.onchange('unit_id')
    def _onchange_unit_id_team(self):
        if self.unit_id and self.unit_id.product_tmpl_id.sr_property_project_id:
            project = self.unit_id.product_tmpl_id.sr_property_project_id
            self.inspector_id = project.default_inspector_id
            self.technician_id = project.default_technician_id

    @api.onchange('category_inm_id')
    def _onchange_category_inm_id(self):
        self.question_inm_id = False

    # --- RESTRICCIONES ---
    @api.constrains('preferred_visit_days', 'preferred_time_slot')
    def _check_saturday_schedule(self):
        for ticket in self:
            if ticket.preferred_visit_days == 'sabado' and ticket.preferred_time_slot in ['pm_early', 'pm_late']:
                raise UserError(_('Atención: Los sábados solo se permiten visitas en la mañana.'))

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('radicado', '/') == '/':
                vals['radicado'] = self.env['ir.sequence'].next_by_code('ghr.radicado') or '/'
        return super().create(vals_list)

    # --- ACCIONES DE ETAPAS ---

    def action_start_diagnostic(self):
        """ Mueve el ticket a la etapa de Diagnóstico """
        self.ensure_one()
        stage = self.env.ref('sr_property_rental_management.stage_diagnostic', raise_if_not_found=False)
        if stage:
            self.stage_id = stage.id
        else:
            raise UserError("No se encontró la etapa: sr_property_rental_management.stage_diagnostic")

    def action_mark_as_closed(self):
        """ Valida firma, mueve a etapa final y envía correo """
        self.ensure_one()
        if not self.signature_client:
            raise UserError("⚠️ No se puede cerrar: Falta la firma de conformidad del cliente.")
        
        closed_stage = self.env.ref('sr_property_rental_management.stage_closed', raise_if_not_found=False)
        if closed_stage:
            self.stage_id = closed_stage.id
            template = self.env.ref('sr_property_rental_management.email_template_ticket_closed', raise_if_not_found=False)
            if template:
                template.send_mail(self.id, force_send=True)
        else:
            raise UserError("No se encontró la etapa final: sr_property_rental_management.stage_closed")

    def write(self, vals):
        """ Bloqueo de seguridad para evitar arrastrar al cierre sin firma """
        if 'stage_id' in vals:
            closed_stage = self.env.ref('sr_property_rental_management.stage_closed', raise_if_not_found=False)
            if closed_stage and vals['stage_id'] == closed_stage.id:
                for record in self:
                    if not record.signature_client:
                        raise UserError("⚠️ No se puede mover a 'Finalizado': Falta la firma del cliente.")
        return super(HelpdeskTicket, self).write(vals)
