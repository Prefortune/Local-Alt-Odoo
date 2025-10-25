# Part of Odoo. See COPYRIGHT & LICENSE files for full copyright and licensing details.

import os
import base64
import zipfile
import tempfile
import shutil
import logging
from odoo import models, fields, api, _
from odoo.exceptions import UserError
from odoo.exceptions import AccessError, MissingError, ValidationError
from io import BytesIO

_logger = logging.getLogger(__name__)


class ProductImageImport(models.TransientModel):
    _name = 'product.image.import'
    _description = 'Bulk Import Product Images'

    zip_file = fields.Binary(string="ZIP File", required=True)
    zip_filename = fields.Char(string="ZIP Filename")
    success_count = fields.Integer(string="Successfully Updated Products", readonly=True)
    fail_count = fields.Integer(string="Failed Updates", readonly=True)


    def import_images(self):
        """Import product images from a zip file using Internal Reference, Barcode"""

        if not self.zip_file:
            raise UserError(_("Please upload a zip file containing images."))
        try:
            zip_data = base64.b64decode(self.zip_file)
            with BytesIO(zip_data) as zip_file_stream:
                with zipfile.ZipFile(zip_file_stream, 'r') as zip_ref:
                    zip_ref.testzip()
        except zipfile.BadZipFile:
            raise ValidationError(_("The uploaded file is not a valid ZIP file."))
        except Exception as e:
            raise ValidationError(_("An error occurred while processing the file: %s") % str(e))

        with tempfile.TemporaryDirectory() as tmp_dir:
            with zipfile.ZipFile(BytesIO(zip_data), 'r') as zip_ref:
                zip_ref.extractall(tmp_dir)

            updated_products = self.env['product.template']
            unmatched_filenames = []

            for root, dirs, files in os.walk(tmp_dir):
                for filename in files:
                    lower_filename = filename.lower().strip()
                    if lower_filename.endswith(('.png', '.jpg', '.jpeg')):
                        identifier = os.path.splitext(filename)[0].strip()
                        _logger.info(f"Processing file: {filename}")

                        product = self._find_product_by_identifier(identifier)
                        if product:
                            _logger.info(f"Updating image for product: {product.display_name}")
                            image_path = os.path.join(root, filename)
                            with open(image_path, 'rb') as img_file:
                                product.image_1920 = base64.b64encode(img_file.read())
                            updated_products |= product
                        else:
                            unmatched_filenames.append(filename)
                    else:
                        unmatched_filenames.append(filename)

        return self.env['import.image.result.wizard'].action_show_results(updated_products, unmatched_filenames)

    def _find_product_by_identifier(self, identifier):
        """Search for a product by internal reference, barcode, or name."""
        product = self.env['product.template'].search(['|', '|',('default_code', '=', identifier),('barcode', '=', identifier),('name', '=', identifier)  # Exact match on name
        ], limit=1)

        if not product:
            product = self.env['product.template'].search([
                ('name', 'ilike', identifier)  # Partial match on name
            ], limit=1)

        return product