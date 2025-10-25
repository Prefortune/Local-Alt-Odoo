# Website Cart Minimum Quantity Module

This module allows you to set minimum quantity requirements for products when customers add them to cart on the website.

## Features

- **Per-Product Minimum Quantity**: Set different minimum quantities for different products
- **Global Minimum Quantity**: Set a global minimum quantity for all products
- **Frontend Validation**: Real-time validation with user-friendly error messages
- **Backend Validation**: Server-side validation for cart operations
- **Configurable Settings**: Easy configuration through product forms and website settings

## Installation

1. Copy the module to your Odoo addons directory
2. Update the app list in Odoo
3. Install the "Website Cart Minimum Quantity" module

## Configuration

### Per-Product Configuration

1. Go to **Inventory > Products > Products**
2. Open any product
3. In the "Website Minimum Quantity Settings" section:
   - Check "Enable Minimum Quantity" to enable validation for this product
   - Set the "Website Minimum Quantity" value (e.g., 5)

### Global Configuration

1. Go to **Website > Configuration > Settings**
2. In the "Minimum Quantity Settings" section:
   - Check "Enable Global Minimum Quantity" to enable global validation
   - Set the "Global Minimum Quantity" value

## Usage

### For Customers

When customers try to add a product to cart with a quantity less than the minimum:

1. **Frontend Validation**: They'll see an error message immediately
2. **Backend Validation**: If they bypass frontend validation, they'll be redirected with an error
3. **Clear Instructions**: Error messages clearly state the minimum quantity required

### For Administrators

- Set minimum quantities per product in the product form
- Configure global minimum quantities in website settings
- Monitor cart behavior through the website

## Example

If you set a minimum quantity of 5 for a product:

- Customer adds 3 items → Error: "Minimum quantity for Product Name is 5. You tried to add 3 items. Please add at least 5 items."
- Customer adds 5 or more items → Successfully added to cart

## Technical Details

- **Models Extended**: `product.template`, `website`, `res.config.settings`
- **Controllers Extended**: `website_sale.controllers.main.WebsiteSale`
- **JavaScript**: Frontend validation with real-time feedback
- **Templates**: Enhanced product and cart templates with error handling

## Dependencies

- website
- website_sale
- sale

## License

LGPL-3
