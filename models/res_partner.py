import uuid

from odoo import _, fields, models
from odoo.exceptions import UserError


class ResPartner(models.Model):
    _inherit = "res.partner"

    warranty_access_token = fields.Char(
        string="Token de Garantia",
        copy=False,
    )

    def _generate_warranty_token(self):
        for partner in self:
            if not partner.warranty_access_token:
                partner.sudo().write({"warranty_access_token": str(uuid.uuid4())})
        return True

    def action_send_warranty_link(self):
        self.ensure_one()
        self._generate_warranty_token()

        if not self.email:
            raise UserError(_("El cliente debe tener un correo electronico configurado."))

        template = self.env.ref(
            "sr_property_rental_management.email_template_warranty_link",
            raise_if_not_found=False,
        )
        if not template:
            raise UserError(_("No se encontro la plantilla de correo de garantia."))

        warranty_url = "%s/warranty/request/%s?db=%s" % (
            self.get_base_url(),
            self.warranty_access_token or "",
            self.env.cr.dbname,
        )
        subject = _("Reporte de Garantia - %s") % (self.name or "")
        body_html = """
            <div style="font-family: Arial, sans-serif; padding: 20px;">
                <p>Hola <strong>{partner}</strong>,</p>
                <p>Para reportar una incidencia de post-venta, usa el siguiente enlace seguro:</p>
                <p style="margin: 20px 0;">
                    <a href="{url}" style="background:#875A7B; color:#fff; text-decoration:none; padding:10px 16px; border-radius:4px;">
                        Reportar Garantia
                    </a>
                </p>
                <p>Si no solicitaste este enlace, puedes ignorar este correo.</p>
            </div>
        """.format(partner=self.name or "", url=warranty_url)

        ctx = {
            "default_model": "res.partner",
            "default_res_ids": [self.id],
            "default_use_template": False,
            "default_template_id": template.id,
            "default_composition_mode": "comment",
            "default_subject": subject,
            "default_body": body_html,
            "default_email_to": self.email or "",
            "force_email": True,
        }
        return {
            "name": _("Enviar Link de Garantia"),
            "type": "ir.actions.act_window",
            "res_model": "mail.compose.message",
            "view_mode": "form",
            "target": "new",
            "context": ctx,
        }
