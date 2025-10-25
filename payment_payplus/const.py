# Part of Odoo. See LICENSE file for full copyright and licensing details.

# Supported currencies (if needed, list them here)
# SUPPORTED_CURRENCIES = [
#     'ILS',  # Israeli Shekel
#     'USD',
#     'EUR',
# ]

# Mapping of transaction statuses to Odoo states
PAYMENT_STATUS_MAPPING = {
    'pending': ['pending'],
    'done': ['approved', 'success'],
    'cancel': ['cancel', 'cancelled'],
    'error': ['error', 'failed'],
}

# Mapping from PayPlus response `method` or `brand_name` to Odoo payment method codes
# Use this to set `payment_method_id` on the transaction
PAYMENT_METHODS_MAPPING = {
    'credit-card': 'payplus',       # Default
    'isracard': 'payplus',
    'visa': 'payplus',
    'mastercard': 'payplus',
    'pl': 'payplus',
    # Add others as you observe them from PayPlus
}

# Optional: Methods to enable by default when provider is activated
DEFAULT_PAYMENT_METHODS_CODES = [
    'manual',
]

