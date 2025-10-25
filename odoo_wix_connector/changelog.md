# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.6.3] - 2024-07-26
### Author: ashish varshney odoo <ashishvarshney.odoo231@webkul.in>

### Fixed
- Invoice and Shipping Date in order import.


## [1.6.2] - 2024-04-16

### Author: krishnansh kapoor odoo <krishnanshkapoor.odoo002@webkul.in>

### Added
- Translation for  German, Spanish and Arabic(ar)

## [1.5.2] - 2024-03-22

Author: adil ali <adilali.odoo366@webkul.in>

### Added
- Implement import orders and products by multiple comma seperated ids in existing field(Object ID)


## [1.4.2] - 2024-03-18

Author: rohit kumar odoo <rohitkumar.odoo828@webkul.in>

### Fixed
- Importing orders using cron and set the next iteration date correctly in the field.


## [1.4.1] - 2024-03-15

Author: rohit kumar odoo <rohitkumar.odoo828@webkul.in>

### Fixed
- Getting payment method for single order.


## [1.4.0] - 2024-03-14

Author: adil ali <adilali.odoo366@webkul.in>

### Added
- Implement the real time cancel the order from Odoo
- Implement the export(create) payment for order from odoo


## [1.3.0] - 2024-03-14

Author: rohit kumar odoo <rohitkumar.odoo828@webkul.in>

### Added
- Getting payment transaction of multiple orders in one API call.

### Changed
- Getting transaction data of single or multiple orders now, previously it was for only one order at a time.


## [1.2.0] - 2024-03-12

Author: rohit kumar odoo <rohitkumar.odoo828@webkul.in>

### Added
1. Getting orders using the ecommerce API [Ref](https://dev.wix.com/docs/rest/api-reference/wix-e-commerce/orders/introduction)
2. Ecommerce order transaction api to get the payment method for order [Ref](https://dev.wix.com/docs/rest/api-reference/wix-e-commerce/order-transactions/list-transactions-for-single-order)
3. Order Ecommerce fullfillment API [Ref](https://dev.wix.com/docs/rest/api-reference/wix-e-commerce/order-fulfillments/create-fulfillment).

### Removed
1. Removed old Wix Store API for the orders, these Wix Store api's are going to be deprecated soon [Ref](https://dev.wix.com/docs/rest/api-reference/wix-stores/orders/create-order)
