from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
import logging
_logger = logging.getLogger(__name__)

class DeliveryCarrier(models.Model):
    _inherit = 'delivery.carrier'

    # Add a field to indicate if the carrier supports split deliveries
    supports_split_delivery = fields.Boolean(string='Supports Split Delivery', default=False, help='Indicates if this carrier supports split deliveries.')
    supports_self_pickup = fields.Boolean(string='Supports Self Pickup', default=False, help='Indicates if this carrier supports Self Pickup.')

    def rate_shipment(self, order):
        res = super(DeliveryCarrier, self).rate_shipment(order)
        split_qty = order.alt_split_delivery_count
        if split_qty >= 1:

            base_price = res.get('price', 0.0)
            carrier_price = res.get('carrier_price', 0.0)

            # Check if shipping is free due to free_over rule
            if base_price == 0.0 and carrier_price > 0.0:
                # First delivery is free, charge for extra
                total_price = (split_qty - 1) * carrier_price
            else:
                # Normal case, no free shipping
                total_price = split_qty * base_price
                
            res['price'] = total_price
            order.write({
                'alt_split_delivery_total_price' : total_price
            })
        _logger.info("Split delivery count for order %s: %s", order.name, order.alt_split_delivery_total_price)
        _logger.info("Calculating shipment rate for order with carrier %s", res)

        return res

    @api.model
    def write(self,vals):
        res = super(DeliveryCarrier,self).write(vals)
        if self.supports_split_delivery == True and self.supports_self_pickup == True:
            raise ValidationError("You Can Not Active Supports Split Delivery And Supports Self Pickup At One Time")
        return res