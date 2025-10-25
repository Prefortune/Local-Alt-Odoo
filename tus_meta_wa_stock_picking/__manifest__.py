{
    "name": "Odoo Meta Whatsapp Stock Picking",
    "version": "17.0",
    "author": "TechUltra Solutions Private Limited",
    "category": "Inventory",
    "live_test_url": "https://www.techultrasolutions.com/blog/news-2/odoo-whatsapp-integration-a-boon-for-business-communication-25",
    "company": "TechUltra Solutions Private Limited",
    "website": "https://www.techultrasolutions.com/",
    "price": 19,
    "currency": "USD",
    "summary": "Whatsapp stock modules allows to send the delivery note to customer by whatsapp message",
    "description": """
        whatsapp all in one and whatsapp stock module will allow user to send the delivery note customer.
    """,
    "depends": ["tus_meta_whatsapp_base", "stock"],
    "data": [
        "data/wa_template.xml",
        "security/stock_security.xml",
        "views/stock_picking.xml",
    ],
    "installable": True,
    "auto_install": False,
    "license": "LGPL-3",
    "images": ["static/description/main_screen.gif"],
    # 'post_init_hook': '_set_image_in_company',
}
