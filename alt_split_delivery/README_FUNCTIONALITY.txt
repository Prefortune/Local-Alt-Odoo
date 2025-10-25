Alt Split Delivery - Module Functionality Summary
===============================================

This document summarizes the actual functionality implemented in the 'Alt Split Delivery' Odoo module, based on the current codebase (models, controllers, views).

1. Split Delivery Core Logic
----------------------------
- The module allows splitting a single sale order into multiple deliveries, each with its own shipping address and shipping cost.
- The number of splits is controlled by the field `alt_split_delivery_count` on the sale order.
- For each split, a record is created in the model `alt.split.delivery`.

2. Models
---------
- **alt.split.delivery**
  - Links to the sale order (`sale_order_id`).
  - Has a delivery index (`alt_delivery_index`) to identify the split number.
  - Stores the shipping address (`alt_partner_shipping_id`).
  - Stores the shipping price for this split (`alt_delivery_price`).
  - Stores additional notes, status, and planned/actual delivery dates.
  - Has a One2many to `alt.split.delivery.line` for the split's order lines.

- **alt.split.delivery.line** (linking table)
  - Links to a split delivery (`split_delivery_id`).
  - Links to a sale order line (`order_line_id`).
  - Stores the quantity of the order line assigned to this split (`quantity`).

- **sale.order** (extension)
  - Field `alt_split_delivery_count`: number of splits requested.
  - Field `alt_split_delivery_ids`: all splits for this order.
  - Field `alt_split_delivery_total_price`: sum of all split shipping prices.
  - Field `has_alt_split_deliveries`: computed, true if there are splits.
  - Methods to create splits, compute totals, and create a single delivery line representing the total shipping cost.

- **sale.order.line** (extension)
  - Field `alt_split_delivery_line_ids`: all split delivery lines referencing this order line.
  - Computed fields for delivered and remaining quantity based on split lines.

3. Controllers
--------------
- JSON routes for updating split count, addresses, and line quantities from the website checkout.
- All updates are performed on the new models and linking table.

4. Views
--------
- Tree, form, and search views for `alt.split.delivery`.
- In the split delivery form, a notebook page shows the split's order lines using the linking table, allowing editing of quantities per line.
- Menu item under Sales > Configuration for managing split deliveries.

5. Website/Checkout
-------------------
- The standard delivery carrier selection is replaced by a UI for split deliveries.
- The customer can select the number of splits and assign addresses and quantities per split.
- The backend is updated via AJAX calls to the new controllers.

6. Security
-----------
- Access rights are defined for both `alt.split.delivery` and `alt.split.delivery.line` for sales users and managers.

7. General
----------
- All fields and models use the `alt_` prefix for consistency.
- The module is independent of Odoo's classic delivery carrier logic.
- All shipping costs are summed and represented as a single delivery line in the order for accounting and reporting.

---
This summary is based strictly on the code and structure of the current module implementation. 