from odoo import api, fields, models


class HelpdeskStageAutomation(models.Model):
    _inherit = "helpdesk.stages"

    wa_template_id = fields.Many2one("wa.template", string="WhatsApp Template")


class HelpdeskTicketAutomation(models.Model):
    _inherit = "sh.helpdesk.ticket"

    def write(self, vals):
        res = super(HelpdeskTicketAutomation, self).write(vals)
        for rec in self:
            if (
                rec.partner_id.mobile
                and vals.get("stage_id")
                and rec.stage_id.wa_template_id
            ):
                composer = (
                    self.env["wa.compose.message"]
                    .with_context(
                        default_model=rec._name,
                        default_res_id=rec.id,
                        default_template_id=rec.stage_id.wa_template_id.id,
                        default_partner_id=rec.partner_id,
                        default_provider_id=rec.stage_id.wa_template_id.provider_id.id,
                    )
                    .create({})
                )
                composer.send_whatsapp_message()
        return res

    @api.model_create_multi
    def create(self, vals_list):
        res = super().create(vals_list)
        for rec in res:
            if rec.partner_id.mobile and rec.stage_id.wa_template_id:
                composer = (
                    self.env["wa.compose.message"]
                    .with_context(
                        default_model=rec._name,
                        default_res_id=rec.id,
                        default_template_id=rec.stage_id.wa_template_id.id,
                        default_partner_id=rec.partner_id,
                        default_provider_id=rec.stage_id.wa_template_id.provider_id.id,
                    )
                    .create({})
                )
                composer.send_whatsapp_message()
        return res
