from odoo import models, fields

class EnginiSettings(models.Model):
    _name = 'engini.settings'
    _description = 'Engini Settings'

    webhook_url = fields.Char(
        string='Webhook URL',
        default='https://webhook.site/edbd06dd-6dea-46f5-a090-a10a10d3ea4e'
    ) 