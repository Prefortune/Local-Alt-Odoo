# Copyright 2016-TODAY Serpent Consulting Services Pvt. Ltd.
# See LICENSE file for full copyright and licensing details.

from odoo.tests import common


class SaleReportProductImageTestCase(common.TransactionCase):

    def setup(self):
        super(SaleReportProductImageTestCase, self).setup()

    def test_sale_report_product(self):
        self.product = self.env.ref("product.product_product_7")
        self.partner = self.env.ref("base.res_partner_2")

        self.product_pricelist = self.env['product.pricelist'].create({'name': "Public Pricelist",})
        self.sale_order = self.env["sale.order"].create(
            {
                "partner_id": self.partner.id,
                "partner_invoice_id": self.partner.id,
                "partner_shipping_id": self.partner.id,
                "pricelist_id": self.product_pricelist.id,
                "alt_print_image": "True",
                "alt_image_sizes": "image_medium",
            }
        )
        self.sale_order_line = self.env["sale.order.line"].create(
            {
                "name": self.product and self.product.name or " ",
                "product_id": self.product and self.product.id or False,
                "product_uom_qty": 2,
                "product_uom": self.product.uom_id.id,
                "price_unit": self.product.list_price,
                "order_id": self.sale_order.id,
                "tax_id": False,
                "alt_image_small": self.product.image_1920,
            }
        )

    def test_hide_summary_in_quote(self):
        """Test the hide summary in quote functionality"""
        self.product = self.env.ref("product.product_product_7")
        self.partner = self.env.ref("base.res_partner_2")

        self.product_pricelist = self.env['product.pricelist'].create({'name': "Public Pricelist",})
        
        # Test with hide summary checked (quotation)
        self.sale_order_quote = self.env["sale.order"].create(
            {
                "partner_id": self.partner.id,
                "partner_invoice_id": self.partner.id,
                "partner_shipping_id": self.partner.id,
                "pricelist_id": self.product_pricelist.id,
                "alt_hide_summary_in_quote": True,
                "state": "draft",  # Quotation state
            }
        )
        
        # Test with hide summary unchecked (quotation)
        self.sale_order_quote_show = self.env["sale.order"].create(
            {
                "partner_id": self.partner.id,
                "partner_invoice_id": self.partner.id,
                "partner_shipping_id": self.partner.id,
                "pricelist_id": self.product_pricelist.id,
                "alt_hide_summary_in_quote": False,
                "state": "draft",  # Quotation state
            }
        )
        
        # Test with hide summary checked (confirmed order)
        self.sale_order_confirmed = self.env["sale.order"].create(
            {
                "partner_id": self.partner.id,
                "partner_invoice_id": self.partner.id,
                "partner_shipping_id": self.partner.id,
                "pricelist_id": self.product_pricelist.id,
                "alt_hide_summary_in_quote": True,
                "state": "sale",  # Confirmed order state
            }
        )
        
        # Verify the functionality
        self.assertTrue(self.sale_order_quote.alt_hide_summary_in_quote)
        self.assertFalse(self.sale_order_quote_show.alt_hide_summary_in_quote)
        self.assertTrue(self.sale_order_confirmed.alt_hide_summary_in_quote)

    def test_greeting_card_report(self):
        """Test the greeting card report functionality"""
        self.product = self.env.ref("product.product_product_7")
        self.partner = self.env.ref("base.res_partner_2")

        self.product_pricelist = self.env['product.pricelist'].create({'name': "Public Pricelist",})
        
        # Test with greeting card message
        self.sale_order_with_greeting = self.env["sale.order"].create(
            {
                "partner_id": self.partner.id,
                "partner_invoice_id": self.partner.id,
                "partner_shipping_id": self.partner.id,
                "pricelist_id": self.product_pricelist.id,
                "greeting_card": "מזל טוב! איחולים חמים ליום ההולדת שלך!",
            }
        )
        
        # Test without greeting card message
        self.sale_order_without_greeting = self.env["sale.order"].create(
            {
                "partner_id": self.partner.id,
                "partner_invoice_id": self.partner.id,
                "partner_shipping_id": self.partner.id,
                "pricelist_id": self.product_pricelist.id,
                "greeting_card": False,
            }
        )
        
        # Verify the functionality
        self.assertEqual(self.sale_order_with_greeting.greeting_card, "מזל טוב! איחולים חמים ליום ההולדת שלך!")
        self.assertFalse(self.sale_order_without_greeting.greeting_card)
        
        # Test greeting card report action
        greeting_action = self.sale_order_with_greeting.action_print_greeting_card()
        self.assertIsNotNone(greeting_action)
        self.assertEqual(greeting_action['type'], 'ir.actions.report')

