# Bizzup Direct Communication

### Technical Name: bizzup_direct_communication

### ['18.0.1.0.0'] - 2025-06-05 | HT01622

- Added development.

### ['18.0.1.1.0'] - 2025-06-18

- Introduced custom logic in the stock.picking model to control and trigger the dropshipping flow upon receipt validation in sub-company.
- Enhanced the action_confirm method in sale.order to handle dropshipping logic.
- Added a custom method to manage dropship PO creation and validation based on receipt validation trigger.
