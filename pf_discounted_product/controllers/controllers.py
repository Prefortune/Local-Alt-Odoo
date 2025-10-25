# -*- coding: utf-8 -*-
from re import X
from odoo import http
from odoo.addons.website_sale.controllers.main import WebsiteSale
from odoo.addons.website_sale_loyalty.controllers.main import WebsiteSale

from odoo.http import request, route
from werkzeug.exceptions import Forbidden, NotFound
from odoo import fields
from odoo.addons.payment import utils as payment_utils
from odoo.tools.json import scriptsafe as json_scriptsafe

import logging
_logger = logging.getLogger(__name__)

class PFWebsiteSale(WebsiteSale):

    @route('/shop/claimreward', type='http', auth='public', website=True, sitemap=False)
    def claim_reward(self, reward_id, code=None, **post):
        order_sudo = request.website.sale_get_order()
        redirect = post.get('r', '/shop/cart')
        if not order_sudo:
            return request.redirect(redirect)

        try:
            reward_id = int(reward_id)
        except ValueError:
            reward_id = None


        reward_sudo = request.env['loyalty.reward'].sudo().browse(reward_id).exists()
        if not reward_sudo:
            return request.redirect(redirect)

        if reward_sudo.multi_product and 'product_id' in post:
            request.update_context(product_id=int(post['product_id']))
        else:
            request.redirect(redirect)

        program_sudo = reward_sudo.program_id
        claimable_rewards = order_sudo._get_claimable_and_showable_rewards()
        coupon = request.env['loyalty.card']
        for coupon_, rewards in claimable_rewards.items():
            if reward_sudo in rewards:
                coupon = coupon_
                if code == coupon.code and (
                    (program_sudo.trigger == 'with_code' and program_sudo.program_type != 'promo_code')
                    or (program_sudo.trigger == 'auto'
                        and program_sudo.applies_on == 'future'
                        and program_sudo.program_type not in ('ewallet', 'loyalty'))
                ):
                    return self.pricelist(code, reward_id=reward_id)
        if coupon and not reward_sudo.reward_type == 'discounted_product':
            self._apply_reward(order_sudo, reward_sudo, coupon)

        if reward_sudo.reward_type == 'discounted_product':
            _logger.info("reward_sudo ---> %s",reward_sudo.description)
            pf_products_to_apply = reward_sudo.pf_products_to_apply
            pf_discounted_product = reward_sudo.pf_discounted_product_id
            pf_discounted_price = reward_sudo.pf_discounted_product_price

            # _logger.info("pf_discounted_price ---> %s",pf_discounted_price)

             # ✅ 1. Check if pf_products_to_apply already exists in cart
            # existing_line = order_sudo.order_line.filtered(lambda l: l.product_id.id == pf_products_to_apply.id)[:1]
            # _logger.info("existing_line ---> %s",existing_line)

            # applyed_product_line = None
            # if not existing_line:
            # Add the required product normally
            applyed_product_line = order_sudo._cart_update(
                product_id=pf_products_to_apply.id,
                add_qty=1,
                set_qty=1,
            )
            _logger.info("applyed_product_line ---> %s",applyed_product_line)
            line_object = request.env['sale.order.line'].sudo().browse(applyed_product_line.get('line_id'))

            # if not pf_discounted_price > line_object.price_unit:
            #     discount_amount = line_object.price_unit - pf_discounted_price
            # else:
            #     discount_amount = line_object.price_unit

            # _logger.info("final price of discount_amount -> %s , %s , %s",discount_amount , line_object.price_unit , pf_discounted_price)
            line_object.write({
                        'price_unit' : pf_discounted_price if reward_sudo.pf_discounted_product_price else line_object.price_unit,
                        'pf_reward_id': reward_sudo.id,
                        'pf_is_discounted_product': True,
                        'reward_id': reward_sudo.id,
            })
                
            
            # # _logger.info("--- applyed_product_line --- %s",applyed_product_line)
            # if not applyed_product_line:
            #     product_price = existing_line.price_unit
            #     _logger.info("if not applyed_product_line product_price---> %s",product_price)

            # else:
            #     line_object = request.env['sale.order.line'].sudo().browse(applyed_product_line.get('line_id'))
            #     _logger.info("else line_object---> %s",line_object)

            #     if line_object:
            #         product_price = line_object.price_unit
            #     else:
            #         product_price = pf_products_to_apply.lst_price

            #     _logger.info("product_price last---> %s",product_price)
                
                    

            # # === חדש: pf_discounted_product_price הוא המחיר הסופי הרצוי ===
            # target_price = pf_discounted_price or 0.0

            # _logger.info("target_price ---> %s",target_price)


            # # כמה צריך להוזיל כדי להגיע למחיר המטרה (לא יורדים מתחת ל-0)
            # discount_amount = product_price - target_price
            # _logger.info("discount_amount ---> %s",discount_amount)

            # if discount_amount <= 0:
            #     # אין מה להנחית (המחיר כבר נמוך/שווה למחיר היעד) → נחזור בלי להוסיף שורת הנחה
            #     return request.redirect(redirect)

            # # עיגול לפי מטבע הזמנה
            # discount_amount = order_sudo.currency_id.round(discount_amount)
            # _logger.info("discount_amount last---> %s",discount_amount)

            # # reward_id = request.env['sale.order'].filtered(lambda x : line for line in x.order_line.reward_id)
            # reward_id = order_sudo.order_line.filtered(lambda l: l.reward_id)
            # _logger.info("reward_id is ---> %s , %s",reward_id , reward_id.name)

            # # יצירת שורת הנחה שלילית בסכום ההפרש
            # request.env['sale.order.line'].sudo().create({
            #     'order_id': order_sudo.id,
            #     'product_id': pf_discounted_product.id,
            #     'product_uom_qty': 1,
            #     'price_unit': -discount_amount,  # שלילי: סכום ההנחה כדי להגיע למחיר היעד
            #     'name': pf_discounted_product.get_product_multiline_description_sale(),
            #     # 'reward_id': reward_sudo.id,
            #     'pf_reward_id': reward_sudo.id,
            #     'pf_is_discounted_product': True,
            # })

           
            
        return request.redirect(redirect)
