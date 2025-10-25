# Part of Odoo. See COPYRIGHT & LICENSE files for full copyright and licensing details.
from odoo import models, fields, api

class ImportImageResultWizard(models.TransientModel):
    _name = 'import.image.result.wizard'
    _description = 'Import Image Result Wizard'

    updated_product_ids = fields.Many2many('product.template', string="Updated Products")
    unmatched_filenames = fields.Text(string="Unmatched Filenames")

    @api.model
    def action_show_results(self, updated_products, unmatched_files):
        """Opens the result wizard with the given updated products and unmatched filenames."""
        wizard = self.create({
            'updated_product_ids': [(6, 0, updated_products.ids)],
            'unmatched_filenames': '\n'.join(unmatched_files)
        })
        return {
            'type': 'ir.actions.act_window',
            'name': 'Import Image Results',
            'res_model': 'import.image.result.wizard',
            'view_mode': 'form',
            'target': 'new',
            'res_id': wizard.id,
        }
