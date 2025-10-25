import xmlrpc.client

url = "http://localhost:8073"  # Adjust the port if necessary
db = "qnb1"
username = 'admin'
password = "admin"

# Authenticate
common = xmlrpc.client.ServerProxy('{}/xmlrpc/2/common'.format(url))
try:
    uid = common.authenticate(db, username, password, {})
except Exception as e:
    print("Authentication failed:", e)

# Connect to the models
models = xmlrpc.client.ServerProxy('{}/xmlrpc/2/object'.format(url))

invoice_id = 86
payment_amount = 100

invoice = models.execute_kw(db, uid, password, 'account.move', 'read', [invoice_id], {
    'fields': ['partner_id', 'journal_id']
})

if not invoice:
    print("Invoice not found!")
else:
    partner_id = invoice[0]['partner_id'][0]
    journal_id = invoice[0]['journal_id'][0]

    payment_register = self.env['account.payment.register'].create({
            'payment_method_line_id': payment_vals['payment_method_line_id'],
            'payment_date': payment_vals['payment_date'],
            'payment_type': payment_vals['payment_type'],
            'partner_id': payment_vals['partner_id'],
            'journal_id': payment_vals['journal_id'],
            'amount': payment_vals['amount'],
            'move_ids': [(6, 0, [invoice.id])],  # Link to the invoice
        })