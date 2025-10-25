from odoo import _, api, fields, models


class BankRecWidget(models.Model):
    _inherit = "bank.rec.widget"

    def _prepare_embedded_views_data(self):
        """ This method adds a default dynamic filter named 'account_tag_filter'
            that filters account move lines (`amls`) by the presence of a specific
            tax tag ID (e.g., 39) in the `tax_tag_ids` field.
         """
        res = super()._prepare_embedded_views_data()
        account_tag_filter = {
            'name': 'account_tag_filter',
            'description': _("Payments to match"),
            'domain':[("account_id.tag_ids", "in", [39])],
            'is_default': True,
        }
        res.get('amls').get('dynamic_filters').append(account_tag_filter)
        return res