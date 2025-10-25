import csv

from odoo.tests.common import TransactionCase
from odoo.tests import tagged


@tagged('post_install', '-at_install', 'product_data_feed')
class TestCustom(TransactionCase):

    def setUp(self):
        super(TestCustom, self).setUp()
        self.product_tmpl_feed = self.env.ref(
            'facebook_shop.feed_facebook_product_template')
        self.product_feed = self.env.ref('facebook_shop.feed_facebook_product')

    def test_00(self):
        res = self.product_tmpl_feed.sudo().generate_data_file()
        feed_lines = [row for row in csv.DictReader(res.splitlines())]
        for line in feed_lines:
            product = self.env['product.template'].browse(int(line['id']))
            self.assertTrue(
                line['price'],
                '%s %s' % (
                    product.list_price, self.product_tmpl_feed.currency_id.name)
            )
