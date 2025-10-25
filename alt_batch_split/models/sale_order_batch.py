from email.policy import default
from pkg_resources import require
from odoo import fields, models, api
import logging
_logger = logging.getLogger(__name__)

class SaleOrderBatch(models.Model):
    _name = 'sale.order.batch'
    _description = 'Sale Order Batch'

    name = fields.Char(required=True)
    sale_order_id = fields.Many2one('sale.order', string="Sale Order", required=True, ondelete="cascade")
    line_ids = fields.One2many('sale.order.batch.line', 'batch_id', string="Batch Lines")
    partner_id = fields.Many2one('res.partner', string="Customer", related='sale_order_id.partner_id', store=True, readonly=True)
    deadline_date = fields.Date(
        string="Deadline",
        help="The last date by which this batch should be delivered."
    )
    note = fields.Text(
        string="Notes",
        help="Additional notes or instructions for this batch."
    )
    task_order_id = fields.Many2one('project.task', string="Task Order Id", required=False, ondelete="cascade")
    delivery_order_id = fields.Many2one('stock.picking', string="Delivery Order Id", required=False, ondelete="cascade")
    delivery_stage = fields.Selection([('draft','Draft'),('ready','Ready'),('done','Done')],default="draft")


class SaleOrderBatchLine(models.Model):
    _name = 'sale.order.batch.line'
    _description = 'Sale Order Batch Line'

    batch_id = fields.Many2one('sale.order.batch', string="Batch", ondelete="cascade")
    product_id = fields.Many2one('product.product', string="Product", store=True)
    quantity = fields.Float(string="Quantity", required=True)
    sale_line_id = fields.Many2one('sale.order.line', string="Sale Order Line", ondelete="cascade")
