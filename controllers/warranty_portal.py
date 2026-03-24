import base64

from odoo import http
from odoo.exceptions import UserError
from odoo.http import request


class SrPropertyWarrantyPortal(http.Controller):
    def _get_partner_properties(self, partner):
        return request.env["product.product"].sudo().search(
            [
                ("is_property", "=", True),
                "|",
                ("product_tmpl_id.owner_ids", "in", partner.id),
                ("product_tmpl_id.current_user_id", "=", partner.id),
            ]
        )

    @http.route(
        ['/property/warranty/request', '/property/warranty/form', '/warranty/request'],
        type='http',
        auth='public',
        website=True
    )
    def warranty_form(self, **kwargs):
        token = (kwargs.get("token") or "").strip()
        if token:
            return request.redirect("/warranty/request/%s" % token)
        if request.env.user._is_public():
            return request.redirect('/web/login?redirect=/property/warranty/request')
        partner = request.env.user.partner_id.sudo()
        partner._generate_warranty_token()
        return request.redirect("/warranty/request/%s" % partner.warranty_access_token)

    @http.route(
        ["/warranty/request/<string:token>"], type="http", auth="public", website=True
    )
    def warranty_token_form(self, token=None, **kwargs):
        partner = request.env["res.partner"].sudo().search(
            [("warranty_access_token", "=", token)], limit=1
        )
        if not partner:
            response = request.render(
                "sr_property_rental_management.warranty_token_invalid",
                {"error_message": "El enlace de garantia no es valido o expiro."},
            )
            response.status_code = 404
            return response

        properties = self._get_partner_properties(partner)
        return request.render(
            "sr_property_rental_management.warranty_ticket_form",
            {
                "partner": partner,
                "properties": properties,
                "token": token,
                "error_message": kwargs.get("error_message"),
            },
        )

    @http.route(['/warranty/submit'], type='http', auth='public', methods=['POST'], csrf=True, website=True)
    def warranty_submit(self, **post):
        token = (post.get("token") or "").strip()
        partner = request.env["res.partner"].sudo().search(
            [("warranty_access_token", "=", token)], limit=1
        )
        if not partner:
            response = request.render(
                "sr_property_rental_management.warranty_token_invalid",
                {"error_message": "El enlace de garantia no es valido o expiro."},
            )
            response.status_code = 404
            return response

        properties = self._get_partner_properties(partner)
        try:
            unit_id = int(post.get("unit_id") or 0)
        except (TypeError, ValueError):
            unit_id = 0
        subject = (post.get('subject') or '').strip()
        description = (post.get('description') or '').strip()
        contact_person_name = (post.get("contact_person_name") or "").strip()
        contact_phone = (post.get("contact_phone") or "").strip()
        preferred_visit_days = (post.get("preferred_visit_days") or "").strip()
        preferred_time_slot = (post.get("preferred_time_slot") or "").strip()
        valid_days = {"lunes", "martes", "miercoles", "jueves", "viernes", "sabado"}
        valid_slots = {"am", "pm_early", "pm_late"}
        preferred_visit_days = preferred_visit_days if preferred_visit_days in valid_days else False
        preferred_time_slot = preferred_time_slot if preferred_time_slot in valid_slots else False

        if not unit_id or unit_id not in properties.ids:
            return request.render(
                "sr_property_rental_management.warranty_ticket_form",
                {
                    "partner": partner,
                    "properties": properties,
                    "token": token,
                    "error_message": "Selecciona una unidad valida asociada al cliente.",
                },
            )

        if not subject:
            return request.render(
                "sr_property_rental_management.warranty_ticket_form",
                {
                    "partner": partner,
                    "properties": properties,
                    "token": token,
                    "error_message": "El asunto es obligatorio.",
                },
            )

        helpdesk_team = request.env['helpdesk.team'].sudo().search([], limit=1)
        if not helpdesk_team:
            return request.render(
                "sr_property_rental_management.warranty_ticket_form",
                {
                    "partner": partner,
                    "properties": properties,
                    "token": token,
                    "error_message": "No hay un equipo de Helpdesk configurado.",
                },
            )

        try:
            ticket = request.env['helpdesk.ticket'].sudo().create({
                'name': subject,
                'description': description,
                'partner_id': partner.id,
                'team_id': helpdesk_team.id,
                'unit_id': unit_id,
                'contact_person_name': contact_person_name,
                'contact_phone': contact_phone,
                'preferred_visit_days': preferred_visit_days or False,
                'preferred_time_slot': preferred_time_slot or False,
            })
        except UserError as e:
            return request.render(
                "sr_property_rental_management.warranty_ticket_form",
                {
                    "partner": partner,
                    "properties": properties,
                    "token": token,
                    "error_message": str(e),
                },
            )

        attachment_ids = []
        uploaded = request.httprequest.files.get("attachments")
        if uploaded and uploaded.filename:
            file_content = uploaded.read()
            if file_content:
                attachment = request.env["ir.attachment"].sudo().create(
                    {
                        "name": uploaded.filename,
                        "datas": base64.b64encode(file_content),
                        "mimetype": uploaded.mimetype or "application/octet-stream",
                        "res_model": "helpdesk.ticket",
                        "res_id": ticket.id,
                    }
                )
                attachment_ids.append(attachment.id)
        if attachment_ids and "ticket_photos" in ticket._fields:
            ticket.sudo().write({"ticket_photos": [(6, 0, attachment_ids)]})

        return request.render(
            'sr_property_rental_management.warranty_ticket_success',
            {
                'ticket': ticket,
                'partner': partner,
            },
        )
