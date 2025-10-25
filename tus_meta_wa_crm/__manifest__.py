{
    "name": "Odoo Meta Whatsapp CRM",
    "version": "17.0",
    "author": "TechUltra Solutions Private Limited",
    "category": "CRM",
    "live_test_url": "https://www.techultrasolutions.com/blog/news-2/odoo-whatsapp-integration-a-boon-for-business-communication-25",
    "company": "TechUltra Solutions Private Limited",
    "website": "https://www.techultrasolutions.com/",
    "price": 19,
    "currency": "USD",
    "summary": "whatsapp crm allow user to send the quotation directly to the customer or leads, it solves the communication gap between the systems.",
    "description": """
Whatsapp crm all in one is used for sending the details of products directly to the customer by single click
    """,
    "depends": ["tus_meta_whatsapp_base", "crm"],
    "data": [
        "security/crm_security.xml",
        "views/crm_lead.xml",
    ],
    "installable": True,
    "auto_install": False,
    "license": "LGPL-3",
    "images": ["static/description/main_screen.gif"],
    # 'post_init_hook': '_set_image_in_company',
}
