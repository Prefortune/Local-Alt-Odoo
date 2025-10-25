# -*- coding: utf-8 -*-

from odoo import api, fields, models

class StockMove(models.Model):
    _inherit = 'stock.move.line'

    def _get_aggregated_product_quantities(self,**kwargs ):
        """Returns dictionary of products and corresponding values of interest + default_code

        Unfortunately because we are working with aggregated data, we have to loop through the
        aggregation to add more values to each datum. This extension adds on the default_code value.

        returns: dictionary {same_key_as_super: {same_values_as_super, default_code}, ...}
        """
        aggregated_move_lines = super()._get_aggregated_product_quantities(**kwargs)
        for aggregated_move_line in aggregated_move_lines:
            for rec in self:
                product_description = rec.move_id.product_description
            # Get the product's default_code (instead of hs_code)
            default = aggregated_move_lines[aggregated_move_line][
                'product'].product_tmpl_id.default_code
            aggregated_move_lines[aggregated_move_line]['default'] = default
            aggregated_move_lines[aggregated_move_line]['product_description'] = product_description

        return aggregated_move_lines


class StockMove(models.Model):
    _inherit = 'stock.move'

    product_description = fields.Char(
        'Product Description',
        compute='_compute_remove_internal_ref'
    )

    def _compute_remove_internal_ref(self):
        for line in self:

            # Check if there's a default_code (internal reference) for the product
            if line.product_id and line.product_id.default_code:
                internal_ref = line.product_id.default_code

                if internal_ref in line.name:

                    cleaned_name = line.name.replace(
                        internal_ref,
                        ''
                    ).strip()

                    cleaned_name = cleaned_name.replace(
                        '[',
                        ''
                    ).replace(
                        ']',
                        ''
                    ).strip()

                    line.product_description = cleaned_name
                else:
                    line.product_description = line.name
            else:
                line.product_description = line.name
