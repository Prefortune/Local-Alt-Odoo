# Part of Softhealer Technologies.
{
    "name": "Create Sale Order From Point Of Sale",
    "author": "Softhealer Technologies",
    "website": "https://www.softhealer.com",
    "support": "support@softhealer.com",
    "category": "Sales",
    "license": "OPL-1",
    "summary": "Create SO From POS Generate SO From POS Sales Order From Point Of Sale Quotation From Point Of Sale Order POS Sale Order Sales From POS Create Sale Order Sales From Point Of Sale Order From POS Sales From Point Of Sales Order From Point Of Sale Order Sale Order From Point Of Sale Order Odoo create sale order from pos Create Sale Order From Point Of Sale module Create SO From POS module Create SO From Point Of Sales Point Of Sale sale order creation Sale Order integration with Point Of Sale Sale Order creation from POS Point Of Sale order management Sale Order generation from POS Odoo",
    "description": """This module allows you to create a quotation/sale order from the point of sale. Sometimes while using POS we need to make the quotation/sale order for that customer then you have to go back and create a quotation/sale order. So we have added a quick button to create quotation/sale order directly from the POS screen.""",
    "version": "0.0.1",
    "depends": ["point_of_sale", "sale_management"],
    "application": True,
    "data": [
        "views/res_config_settings.xml",
    ],
    "assets": {
        "point_of_sale._assets_pos": [
            'sh_pos_create_so/static/src/**/*',
        ],
    },
    "images": ["static/description/background.png", ],
    "auto_install": False,
    "installable": True,
    "price": 25,
    "currency": "EUR",
}
