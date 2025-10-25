from odoo import models, fields, api

class ShopifyOperationWizard(models.TransientModel):
    _name = 'shopify.operation.wizard'
    _description = 'Shopify Operation Wizard'

    shopify_connector_id = fields.Many2one(
        'shopify.connector', 
        string='Shopify Connector', 
        required=True
    )
    operation = fields.Selection(
        [
            ('import_specific_customer', 'Import Specific Customer'),
            ('import_specific_product', 'Import Specific Product'),
            ('import_specific_order', 'Import Specific Order'),
        ], 
        string='Operation', 
        required=True
    )
    record_id = fields.Char(
        string='Record ID',
        help='ID of the record to be imported from Shopify',
        required=True
    )
    def execute_operation(self):
        # Add logic to handle the selected operation
        if self.operation == 'import_specific_customer':
            id = "gid://shopify/Customer/" + self.record_id
            self.shopify_connector_id.import_shopify_customer_by_id(id)
        elif self.operation == 'import_specific_product':
            id = "gid://shopify/Product/" + self.record_id
            self.shopify_connector_id.import_shopify_product_by_id(id)
        elif self.operation == 'import_specific_order':
            id = "gid://shopify/Order/" + self.record_id
            self.shopify_connector_id.import_shopify_order_by_id(id)

        return {
            'effect': {
                'fadeout': 'slow',
                'message': 'Imported successfully',
                'type': 'rainbow_man',
            }
        }