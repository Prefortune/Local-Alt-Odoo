from odoo import models,fields,api
import logging
_logger = logging.getLogger(__name__)
try:
    from zk import ZK, const
except ImportError:
    _logger.error("Please Install pyzk library.")

_logger = logging.getLogger(__name__)


class PosSessionInherit(models.Model):
    _inherit = "pos.session"

    def _loader_params_product_pricelist(self):
        result = super(PosSessionInherit,self)._loader_params_product_pricelist()
        result['search_params']['fields'].append('currency_id')
        return result
    
    def _loader_params_res_currency(self):        
        return {
            'search_params': {
                'domain': [],
                'fields': ['name', 'symbol', 'position', 'rounding', 'rate', 'decimal_places'],
            },
        }
    
    def _get_pos_ui_res_currency(self, params):      
        return self.env['res.currency'].search_read(**params['search_params'])

    def _pos_data_process(self, loaded_data):       
        super()._pos_data_process(loaded_data)
        # _logger.info("...............................loaded_data..........%s",loaded_data)                   
        if self.order_ids:
            order_amount_by_currency = {}
            for each_order_id in self.order_ids:                
                if each_order_id.custom_currency_id:
                    if order_amount_by_currency.get(each_order_id.custom_currency_id.id):
                        order_amount_by_currency[each_order_id.custom_currency_id.id] = order_amount_by_currency[each_order_id.custom_currency_id.id] + each_order_id.amount_total
                    else:
                        order_amount_by_currency[each_order_id.custom_currency_id.id] = each_order_id.amount_total            
            loaded_data['amount_by_currency'] = order_amount_by_currency

 