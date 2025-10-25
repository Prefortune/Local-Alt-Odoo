# -*- coding: utf-8 -*-

from email.policy import default
from odoo import models, fields, api
from odoo.tools import float_round, lazy, str2bool
from collections import defaultdict

import logging
_logger = logging.getLogger(__name__)

class PFLoyaltyReward(models.Model):
    _inherit = 'loyalty.reward'

    reward_type = fields.Selection(
        selection_add=[('discounted_product', 'Discounted Product')],
        ondelete={'discounted_product': 'set default'})
    
    pf_discounted_product_id = fields.Many2one(
        'product.product', string="Discounted Product",
    )
    
    pf_discounted_product_price = fields.Float(
        string="Discounted Price",
        help="Unit price to apply for the discounted product when reward is claimed"
    )
    
    pf_products_to_apply = fields.Many2one(
        'product.product',
        string="Products to Apply"
    )

    def write(self, vals):
        res = super().write(vals)
        if 'description' in vals:
            self._create_missing_discount_line_products()

            # Keep the name of our discount product up to date
            for reward in self:
                if not reward.reward_type == 'discounted_product':
                    reward.discount_line_product_id.write({'name': reward.description})

        if 'active' in vals:
            if vals['active']:
                self.discount_line_product_id.action_unarchive()
            else:
                self.discount_line_product_id.action_archive()
        return res

class PFSaleOrderLines(models.Model):
    _inherit = 'sale.order.line'

    pf_is_discounted_product = fields.Boolean(default=False)
    pf_reward_id = fields.Many2one('loyalty.reward')

    def _is_not_sellable_line(self):
        _logger.info("--- from custom code self.is_reward_line --->>>>>> %s ,%s , %s",self.name , self.is_reward_line , super()._is_not_sellable_line())
        return self.is_reward_line or self.pf_is_discounted_product or super()._is_not_sellable_line()

class SaleOrder(models.Model):
    _inherit = 'sale.order'

    def _get_claimable_rewards(self, forced_coupons=None):
        """
        Fetch all rewards that are currently claimable from all concerned coupons,
         meaning coupons from applied programs and applied rewards or the coupons given as parameter.

        Returns a dict containing the all the claimable rewards grouped by coupon.
        Coupons that can not claim any reward are not contained in the result.
        """
        self.ensure_one()
        all_coupons = forced_coupons or (self.coupon_point_ids.coupon_id | self.order_line.coupon_id | self.applied_coupon_ids)
        has_payment_reward = any(line.reward_id.program_id.is_payment_program for line in self.order_line)
        global_discount_reward = self._get_applied_global_discount()
        active_products_domain = self.env['loyalty.reward']._get_active_products_domain()
        _logger.info("--- active_products_domain --- %s",active_products_domain)
        discountable = lazy(lambda: self._discountable_amount(global_discount_reward))

        total_is_zero = self.currency_id.is_zero(discountable)
        result = defaultdict(lambda: self.env['loyalty.reward'])
        for coupon in all_coupons:
            points = self._get_real_points_for_coupon(coupon)
            for reward in coupon.program_id.reward_ids:
                if (
                    reward.is_global_discount
                    and global_discount_reward
                    and self._best_global_discount_already_applied(
                        global_discount_reward, reward, discountable
                    )
                ):
                    continue
                # Discounts are not allowed if the total is zero unless there is a payment reward, in which case we allow discounts.
                # If the total is 0 again without the payment reward it will be removed.
                is_discount = reward.reward_type == 'discount'
                is_payment_program = reward.program_id.is_payment_program
                if reward.reward_type == 'discounted_product':
                    continue
                if is_discount and total_is_zero and (not has_payment_reward or is_payment_program):
                    continue
                # Skip discount that has already been applied if not part of a payment program
                if is_discount and not is_payment_program and reward in self.order_line.reward_id:
                    continue
                if reward.reward_type == 'product' and not reward.filtered_domain(
                    active_products_domain
                ):
                    continue
                if points >= reward.required_points:
                    result[coupon] |= reward
        return result

    def _apply_program_reward(self, reward, coupon, **kwargs):
        """
        Applies the reward to the order provided the given coupon has enough points.
        This method does not check for program rules.

        This method also assumes the points added by the program triggers have already been computed.
        The temporary points are used if the program is applicable to the current order.

        Returns a dict containing the error message or empty if everything went correctly.
        NOTE: A call to `_update_programs_and_rewards` is expected to reorder the discounts.
        """
        self.ensure_one()
        # Use the old lines before creating new ones. These should already be in a 'reset' state.
        old_reward_lines = kwargs.get('old_lines', self.env['sale.order.line'])
        if reward.is_global_discount:
            global_discount_reward_lines = self._get_applied_global_discount_lines()
            global_discount_reward = global_discount_reward_lines.reward_id
            if (
                global_discount_reward
                and global_discount_reward != reward
                and self._best_global_discount_already_applied(global_discount_reward, reward)
            ):
                return {'error': _("A better global discount is already applied.")}
            elif global_discount_reward and global_discount_reward != reward:
                # Invalidate the old global discount as it may impact the new discount to apply
                global_discount_reward_lines._reset_loyalty(True)
                old_reward_lines |= global_discount_reward_lines
        if not reward.program_id.is_nominative and reward.program_id.applies_on == 'future' and coupon in self.coupon_point_ids.coupon_id:
            return {'error': _('The coupon can only be claimed on future orders.')}
        elif self._get_real_points_for_coupon(coupon) < reward.required_points:
            return {'error': _('The coupon does not have enough points for the selected reward.')}
        reward_vals = self._get_reward_line_values(reward, coupon, **kwargs)
        if not reward.reward_type == 'discounted_product':
            self._write_vals_from_reward_vals(reward_vals, old_reward_lines)
        return {}

    # def _cart_update(self, product_id, line_id=None, add_qty=0, set_qty=0, **kwargs):
        
    #     res = super()._cart_update(
    #         product_id, line_id=line_id, add_qty=add_qty, set_qty=set_qty, **kwargs
    #     )
    #     self._remove_invalid_discounted_rewards()
    #     return res
    

    def _get_claimable_and_showable_rewards_dsicounted_product(self):
        self.ensure_one()

        # 1️⃣ Get all discounted_product rewards for active programs
        discounted_rewards = self.env['loyalty.reward'].search([
            ('reward_type', '=', 'discounted_product'),
            ('program_id.active', '=', True),
            '|',
            ('program_id.website_id', '=', False),
            ('program_id.website_id', '=', self.website_id.id or self.env['website'].get_current_website())
        ])


        _logger.info("--- discounted_rewards--- %s",discounted_rewards)

        # 2️⃣ Remove already applied rewards
        
        applied_rewards = self.order_line.mapped('pf_reward_id')
        _logger.info("--- applied_rewards reward_id--- %s",applied_rewards)
        applied_rewardss = self.order_line.mapped('pf_is_discounted_product')
        _logger.info("--- applied_rewards pf_is_discounted_product --- %s",applied_rewardss)

        discounted_rewards = discounted_rewards - applied_rewards

        valid_rewards = self.env['loyalty.reward']

        # 3️⃣ Check each reward against all its program rules
        for reward in discounted_rewards:
            program = reward.program_id
            rules_ids = program.rule_ids
            reward_valid = True  # Assume reward is valid unless a rule fails

            for rule in rules_ids:
                # Minimum quantity
                if rule.minimum_qty and sum(line.product_uom_qty for line in self.order_line) < rule.minimum_qty:
                    reward_valid = False
                    break
                
                # Minimum amount
                if rule.minimum_amount:
                    order_amount = self.amount_total if rule.minimum_amount_tax_mode == 'incl' else self.amount_untaxed
                    if order_amount < rule.minimum_amount:
                        reward_valid = False
                        break

                # if rule.minimum_amount and self.amount_total < rule.minimum_amount:
                #     reward_valid = False
                #     break
                
                # Product restriction
                if rule.product_ids and not any(line.product_id in rule.product_ids for line in self.order_line):
                    reward_valid = False
                    break
                # Category restriction
                if rule.product_category_id and not any(line.product_id.categ_id in rule.product_category_id for line in self.order_line):
                    reward_valid = False
                    break
                # Product tag restriction
                if rule.product_tag_id and not any(tag in line.product_id.tag_ids for line in self.order_line for tag in rule.product_tag_id):
                    reward_valid = False
                    break

            if reward_valid:
                valid_rewards |= reward

        return valid_rewards

    
    # def _remove_invalid_discounted_rewards(self):

    #     for order in self:
    #         for line in order.order_line.filtered(lambda x : x.pf_reward_id and x.pf_reward_id.reward_type == 'discounted_product'):
    #             reward = line.pf_reward_id
    #             required_product = reward.pf_products_to_apply
    #             # if required product no longer in cart → remove reward line
    #             has_required = any(l.product_id == required_product for l in order.order_line if not l.pf_is_discounted_product)
    #             if not has_required:
    #                 line.unlink()

