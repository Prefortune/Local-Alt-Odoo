import xmlrpc.client

# ----------------------------
# Odoo Connection Details
# ----------------------------
url = "http://localhost:8069/"
db = "enterprise"
username = "admin"
password = "admin"

# ----------------------------
# Authentication
# ----------------------------
common = xmlrpc.client.ServerProxy(f"{url}/xmlrpc/2/common")
uid = common.authenticate(db, username, password, {})

# ----------------------------
# Object Proxy
# ----------------------------
models = xmlrpc.client.ServerProxy(f"{url}/xmlrpc/2/object")

# ----------------------------
# Get Sale Order Data with Lines
# ----------------------------
sale_order_id = 71  # Replace with your sale order ID

# 1. Read Sale Order with all fields
sale_order = models.execute_kw(db, uid, password,
    'sale.order', 'read',
    [[sale_order_id]],  # list of IDs
    {'fields': []}  # empty means all fields
)

if sale_order:
    sale_order = sale_order[0]

    # 2. Get order line IDs
    order_line_ids = sale_order.get('order_line', [])

    # 3. Read Sale Order Lines with all fields
    order_lines = []
    if order_line_ids:
        order_lines = models.execute_kw(db, uid, password,
            'sale.order.line', 'read',
            [order_line_ids],  # list of IDs
            {'fields': []}  # all fields
        )

    # Combine data
    sale_order['order_lines_detail'] = order_lines

    # Print final result
    print("Sale Order:")
    print(sale_order)

else:
    print(f"No sale order found with ID {sale_order_id}")
