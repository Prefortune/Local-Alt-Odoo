{
    "name": "Odoo Meta Whatsapp Purchase",
    "version": "17.0",
    "author": "TechUltra Solutions Private Limited",
    "category": "Purchase",
    "live_test_url": "https://www.techultrasolutions.com/blog/news-2/odoo-whatsapp-integration-a-boon-for-business-communication-25",
    "company": "TechUltra Solutions Private Limited",
    "website": "https://www.techultrasolutions.com/",
    "price": 19,
    "currency": "USD",
    "summary": "Whatsapp Purchase modules allows to send the purchase order by whatsapp message",
    "description": """
        whatsapp all in one and whatsapp purchase module will allow user to send the rfq and purchase order customer and customer.
    """,
    "depends": ["tus_meta_whatsapp_base", "purchase"],
    "data": [
        "security/purchase_security.xml",
        "data/wa_template.xml",
        "views/purchase_order.xml",
    ],
    "installable": True,
    "auto_install": False,
    "license": "LGPL-3",
    "images": ["static/description/main_screen.gif"],
    # 'post_init_hook': '_set_image_in_company',
}
