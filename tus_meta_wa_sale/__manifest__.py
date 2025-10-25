{
    "name": "Odoo Meta Whatsapp Sale",
    "version": "17.0",
    "author": "TechUltra Solutions Private Limited",
    "category": "Sales",
    "live_test_url": "https://www.techultrasolutions.com/blog/news-2/odoo-whatsapp-integration-a-boon-for-business-communication-25",
    "company": "TechUltra Solutions Private Limited",
    "website": "https://www.techultrasolutions.com/",
    "price": 19,
    "currency": "USD",
    "summary": "Whatsapp sales modules allows to send the quotation and sales order by whatsapp message",
    "description": """
        whatsapp all in one and whatsapp sales module will allow user to send the quotation and sales order customer and customer.
    """,
    "depends": ["tus_meta_whatsapp_base", "sale_management"],
    "data": [
        "security/sale_security.xml",
        "data/wa_template.xml",
        "views/sale_order.xml",
    ],
    "installable": True,
    "auto_install": False,
    "license": "LGPL-3",
    "images": ["static/description/main_screen.gif"],
    # 'post_init_hook': '_set_image_in_company',
}
