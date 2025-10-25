# Copyright © 2021 Garazd Creation (<https://garazd.biz>)
# @author: Yurii Razumovskyi (<support@garazd.biz>)
# @author: Iryna Razumovska (<support@garazd.biz>)
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0.html).

import csv
import logging
import mimetypes

from odoo import _, fields, models
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class ImportHelper(models.TransientModel):
    _inherit = 'base_import.helper'

    url = fields.Char(
        default='https://www.facebook.com/products/categories/en_US.txt',
        help='Specify the URL to download a list of product categories (only Plain text .txt)',
        required=True,
    )
    mode = fields.Selection(
        selection_add=[('fb_categ', 'Facebook category')],
    )

    def action_import(self):
        self.ensure_one()
        if self.mode != 'fb_categ':
            return super(ImportHelper, self).action_import()

        mimetype, encoding = mimetypes.guess_type(self.url)
        if mimetype != 'text/plain':
            raise UserError(_('Only the Plain text (.txt) format is allowed.'))

        res = self.open_url(self.url)
        if res['error']:
            raise UserError(_('Error opening URL: %s') % res['error'])
        content = res['content']

        reader = csv.reader(content.split('\n')[1:], delimiter=',')
        for row in reader:
            vals = {
                'code': row[0],
                'name': row[1],
            }
            facebook_category = self.env['product.facebook.category'].search([
                ('code', '=', vals['code']),
            ])
            if not facebook_category:
                self.env['product.facebook.category'].create(vals)
            elif self.do_rewrite:
                facebook_category.write(vals)

        return {
            'name': _('Facebook Categories'),
            'type': 'ir.actions.act_window',
            'res_model': 'product.facebook.category',
            'view_mode': 'list,form',
            'target': 'current',
        }
