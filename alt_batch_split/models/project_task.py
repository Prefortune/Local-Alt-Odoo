from odoo import fields, models, api
import logging
_logger = logging.getLogger(__name__)

class ProjectTask(models.Model):
    _inherit = 'project.task'

    delivery_id = fields.Many2one(
        'stock.picking',
        string="Delivery",
        ondelete='set null'   # <-- This clears the field if the delivery is deleted
    )

    def write(self, vals):
        res =  super().write(vals)
        if 'state' in vals:
            if vals.get('state') == '1_done' and self.delivery_id:
                if self.delivery_id.state != 'done':
                    self.delivery_id.button_validate()
        return res
    

