{
    'name': 'Product Image Bulk Import',
    'category': 'Product',
    'version': '17.0.0.2',
    'author': "TechUltra Solutions Private Limited",
    'company': 'TechUltra Solutions Private Limited',
    'website': "https://www.techultrasolutions.com/",
    'summary': 'Bulk import product images using a zip file with images named after product identifiers',
    'description': """ This module allows users to import product images in bulk via a zip file. The images can be named after the product's Internal Reference, Barcode, or Display name. The module provides feedback on successful imports and notifies if any products are not found..""",
    'depends': ['base', 'product', 'stock'],
    'data': [
        'security/ir.model.access.csv',
        'wizard/import_image_wizard.xml',
        'wizard/import_image_results.xml',
        'views/product_image_import_menu.xml',

    ],
"images": [
        "static/description/main_screen.gif",
    ],
    'category': 'tool',
    'license': 'LGPL-3',
    'price': 16.99,
    'currency': 'EUR',
    'installable': True,
    'auto_install': False,
    'application': True,
}
