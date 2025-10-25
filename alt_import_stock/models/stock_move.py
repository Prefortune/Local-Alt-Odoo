# -*- coding: utf-8 -*-
# Part of alt AV ltd. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, exceptions, _
from odoo.exceptions import UserError
from odoo.tools import float_compare
from odoo.tools.float_utils import float_round, float_is_zero


class StockMove(models.Model):
	_inherit = 'stock.move'

	create_exist_lot = fields.Boolean(string="Import Lot/serial with existing lot",
									  compute="_check_import_lot_serial", store=True)
	create_lot = fields.Boolean(string="Import New Lot/serial",
								compute="_check_import_lot_serial", store=True)

	@api.depends('picking_id.picking_type_id', 'picking_id.picking_type_id.use_create_lots',
				 'picking_id.picking_type_id.use_existing_lots')
	def _check_import_lot_serial(self):
		for rec in self:
			picking_type = rec.picking_id.picking_type_id
			if picking_type.use_create_lots and picking_type.use_existing_lots:
				rec.update({
					'create_exist_lot': True,
					'create_lot': False
				})
			elif picking_type.use_create_lots and not picking_type.use_existing_lots:
				rec.update({
					'create_exist_lot': False,
					'create_lot': True
				})
			else:
				rec.update({
					'create_exist_lot': False,
					'create_lot': False
				})

	def open_serial_wizard(self):
		view = self.env.ref('import_lot_serial_no.lot_wizard_view')
		ctx = {}
		ctx.update({'default_stock_move_id': self.id})
		return {
			'name': _('Import Lots'),
			'type': 'ir.actions.act_window',
			'view_mode': 'form',
			'res_model': 'import.lot.wizard',
			'view_id': view.id,
			'target': 'new',
			'context': ctx
		}

	def _update_reserved_quantity(self, need, location_id, quant_ids=None, lot_id=None, package_id=None, owner_id=None, strict=True):
		""" Create or update move lines and reserves quantity from quants
			Expects the need (qty to reserve) and location_id to reserve from.
			`quant_ids` can be passed as an optimization since no search on the database
			is performed and reservation is done on the passed quants set
		"""
		self.ensure_one()

		if quant_ids is None:
			quant_ids = self.env['stock.quant']
		if isinstance(quant_ids, self.env['stock.lot'].__class__):
			quant_ids = self.env['stock.quant'].search([('lot_id', '=', quant_ids.id)])
		if not lot_id:
			lot_id = self.env['stock.lot']
		if not package_id:
			package_id = self.env['stock.quant.package']
		if not owner_id:
			owner_id = self.env['res.partner']
		quants = quant_ids._get_reserve_quantity(
			self.product_id, location_id, need, product_packaging_id=self.product_packaging_id,
			uom_id=self.product_uom, lot_id=lot_id, package_id=package_id, owner_id=owner_id, strict=strict)
		taken_quantity = 0
		rounding = self.env['decimal.precision'].precision_get('Product Unit of Measure')
		# Find a candidate move line to update or create a new one.
		for reserved_quant, quantity in quants:
			taken_quantity += quantity
			to_update = next((line for line in self.move_line_ids if line._reservation_is_updatable(quantity, reserved_quant)), False)
			if to_update:
				uom_quantity = self.product_id.uom_id._compute_quantity(quantity, to_update.product_uom_id, rounding_method='HALF-UP')
				uom_quantity = float_round(uom_quantity, precision_digits=rounding)
				uom_quantity_back_to_product_uom = to_update.product_uom_id._compute_quantity(uom_quantity, self.product_id.uom_id, rounding_method='HALF-UP')
			if to_update and float_compare(quantity, uom_quantity_back_to_product_uom, precision_digits=rounding) == 0:
				to_update.with_context(reserved_quant=reserved_quant).quantity += uom_quantity
			else:
				if self.product_id.tracking == 'serial':
					vals_list = self._add_serial_move_line_to_vals_list(reserved_quant, quantity)
					if vals_list:
						self.env['stock.move.line'].with_context(reserved_quant=reserved_quant).create(vals_list)
				else:
					self.env['stock.move.line'].with_context(reserved_quant=reserved_quant).create(self._prepare_move_line_vals(quantity=quantity, reserved_quant=reserved_quant))
		return taken_quantity