from odoo import api, models


class MailComposeMessage(models.TransientModel):
    _inherit = "mail.compose.message"

    @api.model
    def default_get(self, fields_list):
        ctx = dict(self.env.context)
        if ctx.get("default_res_id") and not ctx.get("default_res_ids"):
            ctx["default_res_ids"] = [ctx["default_res_id"]]
        ctx.pop("default_res_id", None)
        return super(MailComposeMessage, self.with_context(ctx)).default_get(fields_list)
