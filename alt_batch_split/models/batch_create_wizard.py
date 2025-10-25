from ast import Raise
from curses.ascii import FS
from dataclasses import Field
from odoo import models, fields, api
import logging
_logger = logging.getLogger(__name__)
from odoo.exceptions import UserError, ValidationError

# Wizard 1: Overview
class BatchOverviewWizard(models.TransientModel):
    _name = 'batch.create.wizard'
    _description = 'Overview of Sale Order Batches'

    name = fields.Char()
    sale_order_id = fields.Many2one('sale.order', string="Sale Order", required=True)
    batch_ids = fields.One2many('sale.order.batch', inverse="_inverse_batches", compute="_compute_batches" ,string="Existing Batches")
    stage = fields.Selection([('first','First'),('secound','Secound')],default="first")
    sale_order_line_ids = fields.One2many('batch.create.wizard.line', 'wizard_id', string="Sale Order Lines")
    deadline_date = fields.Date(
        string="Deadline",
        help="The last date by which this batch should be delivered."
    )
    note = fields.Text(
        string="Notes",
        help="Additional notes or instructions for this batch."
    )
    delivery_stage = fields.Selection([('draft','Draft'),('ready','Ready'),('done','Done'),('cancel','Cancel')],default="draft")
    show_sale_order_line_id = fields.One2many(
        related="sale_order_id.order_line",
        string="Sale Order Lines",
        readonly=True
    )


    def action_view_batches(self):
        return {
            'name': 'Batches',
            'type': 'ir.actions.act_window',
            'res_model': 'sale.order.batch',
            'view_mode': 'list,form',
            'domain': [('sale_order_id', '=', self.sale_order_id.id)],
            'context': {'default_sale_order_id': [self.sale_order_id.id]},
            'target': 'current',
        }

    def unlink(self):
        res =  super().unlink()
        return res 

    def sec_stage_view(self):
        self.ensure_one()
        self.stage = 'secound'
        lines = []
        for line in self.sale_order_id.order_line:
            lines.append((0, 0, {
                'sale_order_line_id': line.id,
                'product_id': line.product_id.id,
                'quantity': 1,
            }))
        self.sale_order_line_ids = lines
        return {
            'name': 'Create Batch - Stage 2',
            'type': 'ir.actions.act_window',
            'res_model': 'batch.create.wizard',
            'view_mode': 'form',
            'res_id': self.id,
            'target': 'new',
        }


    def save_this_batch_to_delivery(self):

        """Create deliveries from batches"""
        StockPicking = self.env['stock.picking']
        StockMove = self.env['stock.move']
        PickingType = self.env['stock.picking.type']
        picking_type = PickingType.search([('code', '=', 'outgoing')], limit=1)
        project_model = self.env['project.project']
        warehouse =  self.env['stock.warehouse'].sudo().search([], limit=1)
        count = 0

        

        search_project = project_model.sudo().search([('name','=', f"SO #{self.sale_order_id.name} - {self.sale_order_id.partner_id.name}")],limit=1)
        if not search_project:
            project = project_model.sudo().create({
                'name': f"SO #{self.sale_order_id.name} - {self.sale_order_id.partner_id.name}"
            })
        else:
            project = search_project

        if project:
            stages = self.env['project.task.type'].search([('project_ids', '=', project.id)], limit=1)
            if not stages:
                # Create a default stage and link it to the project
                stage = self.env['project.task.type'].create({
                    'name': 'New',
                    'project_ids': [(6, 0, [project.id])],
                    'sequence': 1,
                })
            else:
                stage = stages
                
        for batch in self.batch_ids:

            _logger.info("---> batch Name - %s",batch.name)
            _logger.info("---> batch Name - %s",batch.delivery_order_id.name)

            if batch.line_ids:
                count += 1 

                # ❗ Delete default delivery pickings (not custom split ones)
                default_pickings = batch.sale_order_id.picking_ids.filtered(
                    lambda p: not p.origin or not p.origin.startswith(f"{batch.sale_order_id.name} - Batch #")
                )
                default_pickings.sudo().unlink()

                delivery_data = {
                    'partner_id': batch.partner_id.id,
                    'picking_type_id': warehouse.out_type_id.id,
                    'location_id': warehouse.lot_stock_id.id,
                    'location_dest_id': batch.partner_id.property_stock_customer.id,
                    'origin': f'{batch.sale_order_id.name} - Batch #',
                    'sale_id': batch.sale_order_id.id,
                }

                _logger.info("----- delivery_data --------- %s",delivery_data)
                

                if not batch.delivery_order_id:
                    created_delivery = StockPicking.create(delivery_data)
                    # 🔹 Create stock moves for each batch line
                    for line in batch.line_ids:
                        StockMove.create({
                            'picking_id': created_delivery.id,
                            'product_id': line.product_id.id,
                            'name': line.product_id.display_name,
                            'product_uom_qty': line.quantity,
                            'product_uom': line.product_id.uom_id.id,
                            'location_id': warehouse.lot_stock_id.id,
                            'location_dest_id': batch.partner_id.property_stock_customer.id,
                            # ⚠️ Map to sale.order.line if available
                            'sale_line_id': line.sale_line_id.id if line.sale_line_id else False,
                        })
                    batch.write({
                        'delivery_order_id' : created_delivery.id
                    })
                else:
                    if batch.delivery_order_id.state != 'done':
                        for line in batch.line_ids:
                            existing_moves = {move.sale_line_id.id: move for move in batch.delivery_order_id.move_ids if move.sale_line_id}
                            existing_moves[line.sale_line_id.id].sudo().write({'product_uom_qty': line.quantity})

                    # batch.delivery_order_id.move_ids.unlink()
                    # for line in batch.line_ids:
                    #     StockMove.create({
                    #         'picking_id': batch.delivery_order_id.id,
                    #         'product_id': line.product_id.id,
                    #         'name': line.product_id.display_name,
                    #         'product_uom_qty': line.quantity,
                    #         'product_uom': line.product_id.uom_id.id,
                    #         'location_id': warehouse.lot_stock_id.id,
                    #         'location_dest_id': batch.partner_id.property_stock_customer.id,
                    #         # ⚠️ Map to sale.order.line if available
                    #         'sale_line_id': line.sale_line_id.id if line.sale_line_id else False,
                    #     })

                get_delivery_id = batch.delivery_order_id
                product_data = []
                for line in batch.line_ids:
                    product_data.append(f"{line.product_id.display_name} (Qty: {line.quantity})")


                _logger.info("-------------- product_data -------- >>> %s",product_data)
                task_data = {
                    'name': f"Task for {batch.sale_order_id.name} Batch #{count} - {batch.name}",
                    'project_id': project.id,
                    'stage_id': stage.id,
                    'delivery_id' : get_delivery_id.id,
                    'date_deadline' : batch.deadline_date,
                    'description' : "<br/>".join(product_data),
                }

                _logger.info("----- task_data --------- %s",task_data)


                if not batch.task_order_id:
                    task = self.env['project.task'].sudo().create(task_data)
                    batch.write({
                        'task_order_id' : task.id
                    })
                else:
                    batch.task_order_id.sudo().write(task_data)


                sale_order = batch.sale_order_id
                sale_order.write({
                    'project_id': project.id
                })
        return {'type': 'ir.actions.act_window_close'}


    def save_this_batch_in_lines(self):

        if not self.name:
            raise ValidationError("Name Is Required")
        
        """Create a batch from SO lines (stage 2)"""
        self.ensure_one()

        if not self.sale_order_line_ids:
            return

        # Collect original order quantities
        actual_order_qty = {}
        for so_line in self.sale_order_id.order_line:
            product = so_line.product_id
            actual_order_qty[product.id] = so_line.product_uom_qty
        _logger.info("--- actual_order_qty --- %s", actual_order_qty)

        # Collect new batch lines quantities
        new_lines_with_qty = {}
        for line in self.sale_order_line_ids:
            if line.quantity > 0:
                product_id = line.product_id.id
                new_lines_with_qty[product_id] = new_lines_with_qty.get(product_id, 0) + line.quantity

        # ✅ Validation: check if any product exceeds allowed qty
        for product_id, new_qty in new_lines_with_qty.items():
            allowed_qty = actual_order_qty.get(product_id, 0.0)
            if new_qty > allowed_qty:
                product_name = self.env['product.product'].browse(product_id).display_name
                raise UserError(
                    f"You cannot assign more than {allowed_qty} units "
                    f"for product '{product_name}'. You tried to assign {new_qty}."
                )

        # create batch
        batch = self.env['sale.order.batch'].create({
            'name' : self.name,
            'sale_order_id': self.sale_order_id.id,
            'partner_id': self.sale_order_id.partner_id.id,
            'deadline_date': self.deadline_date,
            'note': self.note,
        })

        # create batch lines
        for line in self.sale_order_line_ids:
            if line.quantity > 0:
                line_data = {
                    'batch_id': batch.id,
                    'product_id': line.product_id.id,
                    'quantity': line.quantity,
                    'sale_line_id': line.sale_order_line_id.id, 
                }
                self.env['sale.order.batch.line'].create(line_data)

        
        self.stage = 'first'
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'batch.create.wizard',
            'view_mode': 'form',
            'res_id': self.id,
            'target': 'new',
            'context': {'sale_order_id': self.sale_order_id.id},
        }

        


    @api.depends('sale_order_id')
    def _compute_batches(self):
        """Compute existing batch lines for the selected sale order"""
        for wiz in self:
            if wiz.sale_order_id:
                _logger.info("--- Computing batch lines for sale order: %s ---", wiz.sale_order_id.name)
                batches = self.env['sale.order.batch'].search([('sale_order_id', '=', wiz.sale_order_id.id)])
                if batches.exists():
                    wiz.batch_ids = batches      
                else:
                    wiz.batch_ids = False          
            else:
                wiz.batch_ids = False

    def _inverse_batches(self):
        pass
        


    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)
        if self.env.context.get('sale_order_id'):
            order = self.env['sale.order'].browse(self.env.context['sale_order_id'])
            res['sale_order_id'] = order.id
        return res
    
    @api.onchange('sale_order_id')
    def _onchange_sale_order_id(self):
        """Populate sale_order_line_ids for stage 2"""
        for wiz in self:
            if wiz.stage == 'second' and wiz.sale_order_id:
                lines = []
                for line in wiz.sale_order_id.order_line:
                    lines.append((0, 0, {
                        'sale_order_line_id': line.id,
                        'product_id': line.product_id.id,
                        'quantity': line.product_uom_qty,
                    }))
                wiz.sale_order_line_ids = lines


class BatchCreateWizardLine(models.TransientModel):
    _name = 'batch.create.wizard.line'
    _description = 'Wizard Line for Sale Order'

    wizard_id = fields.Many2one('batch.create.wizard', string="Wizard")
    sale_order_line_id = fields.Many2one('sale.order.line', string="Sale Order Line")
    product_id = fields.Many2one('product.product', string="Product", readonly=True)
    quantity = fields.Float(string="Quantity")

    
