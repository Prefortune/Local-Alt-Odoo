from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError
import logging
_logger = logging.getLogger(__name__)

class AltPurchaseSplitWizard(models.TransientModel):
    _name = 'alt.purchase.split.wizard'
    _description = 'Alt Purchase Split Delivery Wizard'

    purchase_order_id = fields.Many2one('purchase.order', string='Purchase Order', required=True)
    split_count = fields.Integer(string='Number of Batches', required=True, default=1)
    
    # Wizard state
    state = fields.Selection([
        ('count', 'Select Number of Batches'),
        ('configure', 'Configure Batches'),
        ('saved', 'Saved Configuration'),
        ('completed', 'Completed')
    ], string='State', default='count')
    
    # Batch fields
    split_delivery_ids = fields.One2many('alt.purchase.split.wizard.line', 'wizard_id', string='Delivery Batches')
    
    # Products from order
    purchase_order_line_ids = fields.One2many('alt.purchase.split.wizard.product.line', 'wizard_id', string='Products from Order')
    
    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)
        if 'purchase_order_id' in self.env.context:
            res['purchase_order_id'] = self.env.context['purchase_order_id']
            res['split_count'] = self.env['purchase.order'].browse(res['purchase_order_id']).alt_split_delivery_count or 1
        return res
    
    def action_confirm_split_count(self):
        """Confirm number of batches and proceed to next step"""
        self.ensure_one()
        
        if self.split_count <= 0:
            raise ValidationError(_('Number of batches must be greater than 0'))
        
        # Create products from order
        self.purchase_order_line_ids = [(5, 0, 0)]  # Clear existing lines
        
        for line in self.purchase_order_id.order_line:
            if line.product_id and line.product_qty > 0:
                self.purchase_order_line_ids = [(0, 0, {
                    'product_id': line.product_id.id,
                    'product_name': line.name,
                    'original_qty': line.product_qty,
                    'remaining_qty': line.product_qty,
                    'product_uom': line.product_uom.name,
                })]
        
        # Create batch lines
        self.split_delivery_ids = [(5, 0, 0)]  # Clear existing lines
        
        for i in range(1, self.split_count + 1):
            # Create products for batch
            product_lines = []
            for product_line in self.purchase_order_line_ids:
                product_lines.append((0, 0, {
                    'product_id': product_line.product_id.id,
                    'product_name': product_line.product_name,
                    'product_qty': 0.0,  # Will be filled manually
                    'product_uom': product_line.product_uom,
                }))
            
            self.split_delivery_ids = [(0, 0, {
                'delivery_index': i,
                'partner_id': self.purchase_order_id.partner_id.id,
                'street': self.purchase_order_id.partner_id.street or '',
                'street2': self.purchase_order_id.partner_id.street2 or '',
                'city': self.purchase_order_id.partner_id.city or '',
                'zip': self.purchase_order_id.partner_id.zip or '',
                'product_line_ids': product_lines,
            })]
        
        # Move to next step
        self.state = 'configure'
        
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'alt.purchase.split.wizard',
            'res_id': self.id,
            'view_mode': 'form',
            'target': 'new',
        }
    
    def action_recalculate(self):
        """Return to batch number selection"""
        self.ensure_one()
        
        return {
            'type': 'ir.actions.act_window',
            'name': _('Recalculate'),
            'res_model': 'alt.purchase.split.wizard.recalculate',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_wizard_id': self.id,
                'default_purchase_order_id': self.purchase_order_id.id,
            }
        }
    
    def action_save_batches(self):
        """Save batch configuration and update purchase order"""
        self.ensure_one()
        
        if self.split_count <= 0:
            raise ValidationError(_('Number of batches must be greater than 0'))
        
        # Update purchase order with batch count
        self.purchase_order_id.write({
            'alt_split_delivery_count': self.split_count,
        })
        
        # Save wizard state for future access
        self.write({
            'state': 'saved',
        })
        
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Saved!'),
                'message': _('Batch configuration saved for order %s') % self.purchase_order_id.name,
                'type': 'success',
                'sticky': False,
            }
        }
    
    def action_create_split_deliveries(self):
        """Create actual batches and pickings"""
        self.ensure_one()
        
        if self.split_count <= 0:
            raise ValidationError(_('Number of batches must be greater than 0'))
        
        # Delete existing batches
        existing_splits = self.env['alt.purchase.split.delivery'].search([
            ('purchase_order_id', '=', self.purchase_order_id.id)
        ])
        existing_splits.unlink()
        
        # Delete existing batch pickings
        existing_pickings = self.purchase_order_id.picking_ids.filtered(lambda p: 'Batch' in (p.origin or ''))
        existing_pickings.sudo().unlink()
        
        # Create new batches
        warehouse = self.purchase_order_id.warehouse_id or self.env['stock.warehouse'].search([], limit=1)
        israel = self.env['res.country'].sudo().search([('code', '=', 'IL')], limit=1)
        
        for line in self.split_delivery_ids:
            # Create or update partner
            if line.partner_id:
                partner = line.partner_id
                partner.write({
                    'street': line.street,
                    'street2': line.street2,
                    'city': line.city,
                    'zip': line.zip,
                })
            else:
                partner = self.env['res.partner'].create({
                    'name': f"{self.purchase_order_id.partner_id.name} - Batch {line.delivery_index}",
                    'parent_id': self.purchase_order_id.partner_id.id,
                    'type': 'delivery',
                    'street': line.street,
                    'street2': line.street2,
                    'city': line.city,
                    'zip': line.zip,
                    'country_id': israel.id,
                })
            
            # Create new picking
            picking = self.env['stock.picking'].create({
                'partner_id': partner.id,
                'picking_type_id': warehouse.in_type_id.id,  # Incoming
                'location_id': partner.property_stock_supplier.id,
                'location_dest_id': warehouse.lot_stock_id.id,
                'origin': f"{self.purchase_order_id.name} - Batch {line.delivery_index}",
                'purchase_id': self.purchase_order_id.id,
            })
            
            # Create batch management record
            self.env['alt.purchase.split.delivery'].create({
                'purchase_order_id': self.purchase_order_id.id,
                'alt_delivery_index': line.delivery_index,
                'picking_id': picking.id,
                'alt_scheduled_date': line.scheduled_date,
                'alt_delivery_notes': line.delivery_notes,
            })
        
        # Update wizard state
        self.write({
            'state': 'completed',
        })
        
        _logger.info(f"Created {self.split_count} split deliveries for purchase order {self.purchase_order_id.name}")
        
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Success!'),
                'message': _('Created %d delivery batches for order %s') % (self.split_count, self.purchase_order_id.name),
                'type': 'success',
                'sticky': False,
            }
        }


class AltPurchaseSplitWizardLine(models.TransientModel):
    _name = 'alt.purchase.split.wizard.line'
    _description = 'Alt Purchase Split Wizard Line'

    wizard_id = fields.Many2one('alt.purchase.split.wizard', string='Wizard', required=True, ondelete='cascade')
    delivery_index = fields.Integer(string='Batch Number', required=True, default=1)
    
    # Delivery address
    partner_id = fields.Many2one('res.partner', string='Partner')
    street = fields.Char(string='Street')
    street2 = fields.Char(string='Street 2')
    city = fields.Char(string='City')
    zip = fields.Char(string='ZIP')
    
    # Additional details
    scheduled_date = fields.Datetime(string='Expected Delivery Date')
    delivery_notes = fields.Text(string='Batch Notes')
    
    # Products in batch
    product_line_ids = fields.One2many('alt.purchase.split.wizard.delivery.product', 'delivery_line_id', string='Products in Batch')
    
    # Products display as tags
    products_display = fields.Char(string='Products in Batch', compute='_compute_products_display')
    
    @api.depends('product_line_ids.product_name', 'product_line_ids.product_qty')
    def _compute_products_display(self):
        """Calculate products display as tags"""
        for record in self:
            if record.product_line_ids:
                products = []
                for line in record.product_line_ids.filtered(lambda l: l.product_qty > 0):
                    products.append(f"{line.product_name} ({line.product_qty})")
                record.products_display = ', '.join(products)
            else:
                record.products_display = ''
    
    def _has_products(self):
        """Check if batch has any products with quantity > 0"""
        return any(line.product_qty > 0 for line in self.product_line_ids)


class AltPurchaseSplitWizardProductLine(models.TransientModel):
    _name = 'alt.purchase.split.wizard.product.line'
    _description = 'Alt Purchase Split Wizard Product Line'

    wizard_id = fields.Many2one('alt.purchase.split.wizard', string='Wizard', required=True, ondelete='cascade')
    product_id = fields.Many2one('product.product', string='Product', required=True)
    product_name = fields.Char(string='Product Name', readonly=True)
    original_qty = fields.Float(string='Original Quantity', readonly=True)
    remaining_qty = fields.Float(string='Remaining Quantity', readonly=True)
    product_uom = fields.Char(string='Unit of Measure', readonly=True)


class AltPurchaseSplitWizardDeliveryProduct(models.TransientModel):
    _name = 'alt.purchase.split.wizard.delivery.product'
    _description = 'Alt Purchase Split Wizard Delivery Product'

    delivery_line_id = fields.Many2one('alt.purchase.split.wizard.line', string='Batch', required=True, ondelete='cascade')
    product_id = fields.Many2one('product.product', string='Product', required=True)
    product_name = fields.Char(string='Product Name', readonly=True)
    product_qty = fields.Float(string='Quantity in Batch', default=0.0)
    product_uom = fields.Char(string='Unit of Measure', readonly=True)
    
    @api.onchange('product_qty')
    def _onchange_product_qty(self):
        """Update remaining quantity"""
        if self.product_id and self.product_qty >= 0:
            # Calculate remaining quantity
            wizard = self.delivery_line_id.wizard_id
            total_allocated = sum(line.product_qty for line in wizard.split_delivery_ids.product_line_ids if line.product_id == self.product_id)
            product_line = wizard.purchase_order_line_ids.filtered(lambda l: l.product_id == self.product_id)
            if product_line:
                remaining = product_line.original_qty - total_allocated
                product_line.remaining_qty = remaining
                
                # Check that we did not exceed original quantity
                if remaining < 0:
                    return {
                        'warning': {
                            'title': _('Excess Quantity'),
                            'message': _('Total quantity of product %s exceeded original quantity (%s)') % (self.product_id.name, product_line.original_qty)
                        }
                    }
                
                # Update all other products
                for other_product_line in wizard.purchase_order_line_ids:
                    if other_product_line.product_id != self.product_id:
                        other_total = sum(line.product_qty for line in wizard.split_delivery_ids.product_line_ids if line.product_id == other_product_line.product_id)
                        other_product_line.remaining_qty = other_product_line.original_qty - other_total
    
    @api.model_create_multi
    def create(self, vals_list):
        """Update remaining quantity after creation"""
        records = super().create(vals_list)
        for record in records:
            if record.product_id and record.product_qty >= 0:
                record._update_remaining_qty()
        return records
    
    def write(self, vals):
        """Update remaining quantity after update"""
        result = super().write(vals)
        if 'product_qty' in vals:
            for record in self:
                if record.product_id and record.product_qty >= 0:
                    record._update_remaining_qty()
        return result
    
    def _update_remaining_qty(self):
        """Update remaining quantity"""
        wizard = self.delivery_line_id.wizard_id
        for product_line in wizard.purchase_order_line_ids:
            total_allocated = sum(line.product_qty for line in wizard.split_delivery_ids.product_line_ids if line.product_id == product_line.product_id)
            product_line.remaining_qty = product_line.original_qty - total_allocated


class AltPurchaseSplitWizardRecalculate(models.TransientModel):
    _name = 'alt.purchase.split.wizard.recalculate'
    _description = 'Alt Purchase Split Wizard Recalculate'

    wizard_id = fields.Many2one('alt.purchase.split.wizard', string='Wizard', required=True)
    purchase_order_id = fields.Many2one('purchase.order', string='Purchase Order', required=True)
    
    def action_confirm_recalculate(self):
        """Confirm recalculation"""
        self.ensure_one()
        
        # Delete all existing data
        self.wizard_id.split_delivery_ids = [(5, 0, 0)]
        self.wizard_id.purchase_order_line_ids = [(5, 0, 0)]
        
        # Return to first step
        self.wizard_id.state = 'count'
        
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'alt.purchase.split.wizard',
            'res_id': self.wizard_id.id,
            'view_mode': 'form',
            'target': 'new',
        }
    
    def action_cancel_recalculate(self):
        """Cancel recalculation"""
        return {'type': 'ir.actions.act_window_close'}
