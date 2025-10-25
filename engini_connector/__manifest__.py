{
    "name": "Engini Connector",
    "version": "1.0",
    "summary": "Send sale orders to Engini webhook",
    "category": "Sales",
    "depends": ["sale", "account"],
    "data": [
        "security/ir.model.access.csv",
        "data/webhook_action.xml",
        "views/sale_views.xml",
        "views/engini_bulk_runner_view.xml",
    ],
    "installable": True,
    "application": False,
    "auto_install": True,
    "license": "LGPL-3"
}
