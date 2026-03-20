from odoo import http
from odoo.http import request


class SrPropertyWarrantyPortal(http.Controller):
    def _get_partner_units(self):
        if request.env.user._is_public():
            return request.env['product.product'].sudo().browse([])
        partner = request.env.user.partner_id
        return request.env['product.product'].sudo().search([
            ('is_property', '=', True),
            ('product_tmpl_id.owner_ids', 'in', partner.id),
        ])

    @http.route('/property/warranty/request', type='http', auth='public', website=True)
    def warranty_form(self, **kwargs):
        if request.env.user._is_public():
            return request.redirect('/web/login?redirect=/property/warranty/request')
        units = self._get_partner_units()
        return request.render('sr_property_rental_management.warranty_ticket_form', {
            'units': units,
            'error_message': kwargs.get('error_message'),
            'success_message': kwargs.get('success_message'),
        })

    @http.route('/property/warranty/unit_info/<int:unit_id>', type='http', auth='public', website=True)
    def warranty_unit_info(self, unit_id, **kwargs):
        if request.env.user._is_public():
            return request.make_json_response({'project_name': ''})
        unit = request.env['product.product'].sudo().browse(unit_id)
        project_name = ''
        partner = request.env.user.partner_id
        if unit.exists() and partner in unit.product_tmpl_id.owner_ids:
            project_name = unit.product_tmpl_id.sr_property_project_id.name or ''
        return request.make_json_response({'project_name': project_name})

    @http.route('/property/warranty/submit', type='http', auth='public', methods=['POST'], csrf=True, website=True)
    def warranty_submit(self, **post):
        if request.env.user._is_public():
            return request.redirect('/web/login?redirect=/property/warranty/request')
        units = self._get_partner_units()
        partner = request.env.user.partner_id
        unit_id = int(post.get('unit_id') or 0)
        subject = (post.get('subject') or '').strip()
        description = (post.get('description') or '').strip()

        if not unit_id or unit_id not in units.ids:
            return request.render('sr_property_rental_management.warranty_ticket_form', {
                'units': units,
                'error_message': 'Selecciona una unidad valida de tu propiedad.',
            })

        if not subject:
            return request.render('sr_property_rental_management.warranty_ticket_form', {
                'units': units,
                'error_message': 'El asunto es obligatorio.',
            })

        helpdesk_team = request.env['helpdesk.team'].sudo().search([], limit=1)
        if not helpdesk_team:
            return request.render('sr_property_rental_management.warranty_ticket_form', {
                'units': units,
                'error_message': 'No hay un equipo de Helpdesk configurado.',
            })

        ticket = request.env['helpdesk.ticket'].sudo().create({
            'name': subject,
            'description': description,
            'partner_id': partner.id,
            'team_id': helpdesk_team.id,
            'unit_id': unit_id,
        })

        return request.render('sr_property_rental_management.warranty_ticket_success', {
            'ticket': ticket,
        })
