{
    "name": "Engini Connector",
    "version": "1.0",
    "summary": "Send sale orders to Engini webhook",
    "category": "Sales",
    "depends": ["sale", "account"],
    "data": [
        "security/ir.model.access.csv",
        "views/engini_settings_view.xml",
        "views/engini_sync_history_view.xml",
        "views/engini_bulk_runner_view.xml",
        "data/webhook_action.xml",

        "views/sale_order_extension_view.xml",
        "views/engini_menu.xml",
    ],
    "installable": True,
    "application": True,
    "auto_install": True,
    "web_icon": "engini_connector/static/description/icon.png",
    "license": "LGPL-3"
}
