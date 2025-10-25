Alt Split Delivery - Module Functionality Summary
===============================================

This document summarizes the actual functionality implemented in the 'Alt Split Delivery' Odoo module, based on the current codebase (models, controllers, views).

1. Split Delivery Core Logic
----------------------------
- The module allows customers to purchase multiple delivery services for a single order.
- The number of deliveries is controlled by the field `alt_split_delivery_count` on the sale order.
- Each delivery can be sent to a different address and is managed through stock pickings.
- The module integrates with Odoo's standard delivery carrier system.

2. Models
---------
- **alt.split.delivery** (Legacy model - partially used)
  - Links to the sale order (`sale_order_id`).
  - Has a delivery index (`alt_delivery_index`) to identify the split number.
  - Stores the shipping address (`alt_partner_shipping_id`).
  - Stores the shipping price for this split (`alt_delivery_price`).
  - Stores additional notes, status, and planned/actual delivery dates.
  - Has a One2many to `alt.split.delivery.line` for the split's order lines.
  - Includes workflow actions (confirm, in_transit, delivered, cancel).

- **alt.split.delivery.line** (Linking table - legacy)
  - Links to a split delivery (`split_delivery_id`).
  - Links to a sale order line (`order_line_id`).
  - Stores the quantity of the order line assigned to this split (`quantity`).

- **sale.order** (extension)
  - Field `alt_split_delivery_count`: number of deliveries requested (default: 1).
  - Field `alt_split_delivery_note`: readonly delivery note field.
  - Field `alt_split_delivery_total_price`: sum of all split shipping prices.
  - Field `alt_split_delivery_url`: computed URL for split delivery management.
  - Field `customer_delivery_date`: customer's expected delivery date.
  - Field `greeting_card`: text field for greeting card message.
  - Field `delivery_note`: text field for delivery instructions.
  - Methods to handle delivery count changes and pricing calculations.

- **delivery.carrier** (extension)
  - Field `supports_split_delivery`: boolean indicating if carrier supports split deliveries.
  - Field `supports_self_pickup`: boolean indicating if carrier supports self pickup.
  - Enhanced `rate_shipment` method to calculate pricing for multiple deliveries.
  - Validation to prevent both split delivery and self pickup being enabled simultaneously.

3. Controllers
--------------
- **DeliveryController**: JSON routes for website functionality
  - `/get/current/split_qty`: Returns current split delivery count
  - `/get/schedule/date`: Returns customer delivery date
  - `/get/notes`: Returns greeting card and delivery notes

- **WebsiteSaleCustom**: Customer interaction endpoints
  - `/shop/set_delivery_date`: Set customer expected delivery date
  - `/shop/set_gretting_note`: Set greeting card message
  - `/shop/set_delivery_note`: Set delivery instructions

- **DeliveryInherit**: Enhanced delivery method selection
  - `/shop/set_delivery_method`: Modified to handle split delivery count

- **SplitDeliveryController**: Portal management (get_delivery_address.py)
  - `/my/orders/<order_id>/split_delivery`: Portal page for managing split deliveries
  - `/my/orders/<order_id>/split_delivery/save`: Save split delivery configurations
  - Creates/updates stock pickings for each delivery split
  - Manages delivery addresses and product quantities per split

4. Views
--------
- **alt.split.delivery**: Tree, form, and search views with workflow buttons
- **sale.order**: Extended form view with Split Deliveries tab
  - Shows delivery count, total price, and management URL
  - Displays picking records
  - Includes customer delivery date and notes fields
- **delivery.carrier**: Extended form with split delivery and self pickup options
- **Website templates**: Custom checkout forms for delivery quantity, date, and notes

5. Website/Checkout
-------------------
- Custom delivery form replaces standard carrier selection
- Quantity selector for number of deliveries
- Date picker for scheduled delivery
- Greeting card and delivery notes inputs
- Warning message about address collection after payment
- Integration with delivery carriers that support split delivery

6. Portal Management
--------------------
- Dedicated portal page for managing split deliveries after order confirmation
- Interface for setting different addresses for each delivery
- Product quantity assignment per delivery split
- Validation to ensure quantities don't exceed ordered amounts
- Creates stock pickings with "Split #X" origin format

7. Security
-----------
- Portal access restricted to order partners and their parents
- Manager access for sales team managers
- No specific access rights defined in CSV (relies on standard Odoo permissions)

8. General
----------
- All fields use the `alt_` prefix for consistency
- Integrates with standard Odoo delivery and stock systems
- Uses stock pickings for actual delivery management
- Supports Hebrew language interface
- Compatible with Odoo 18 community edition

---
This summary is based strictly on the code and structure of the current module implementation. 