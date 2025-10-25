from odoo import models, fields, api

class CloverWebhookLog(models.Model):
    _name = "clover.webhook.log"
    _description = "Clover Webhook Log"

    payload = fields.Text("Payload")
    params = fields.Text("Query Parameters")
    response = fields.Text("Response")
    status = fields.Selection([('success','Success'),('error','Error')], default='success')
    created_at = fields.Datetime(default=fields.Datetime.now)