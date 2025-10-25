# Part of Odoo. See COPYRIGHT & LICENSE files for full copyright and licensing details.
from odoo import models, fields, api

class ImportImageWizard(models.TransientModel):
    _name = 'import.image.wizard'
    _description = 'Import Product Images Wizard'

    zip_file = fields.Binary('Upload Zip File', required=True)
    zip_filename = fields.Char('Zip Filename')

    def action_import_images(self):
        """Trigger the import process"""
        import_result = self.env['product.image.import'].create({
            'zip_file': self.zip_file,
            'zip_filename': self.zip_filename,
        }).import_images()

        return import_result
