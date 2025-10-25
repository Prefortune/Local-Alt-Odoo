from odoo import models, api, _, fields
from odoo.exceptions import ValidationError

class PosConfig(models.Model):
    _inherit="pos.config"

    partial_payment = fields.Boolean(string='Allow Partial Payment',
                                     default=True,
                                     help="If enabled, the Point of Sale system"
                                          "allows partial payments for orders.")
    
    def _get_available_product_domain(self):
        domain = super()._get_available_product_domain()
        # domain.append(('qty_available','>',0))
        # domain.append(('active','=',True))
        return domain


    @api.constrains('pricelist_id', 'use_pricelist', 'available_pricelist_ids', 'journal_id', 'invoice_journal_id', 'payment_method_ids')
    def _check_currencies(self):
        for config in self:
            if config.use_pricelist and config.pricelist_id and config.pricelist_id not in config.available_pricelist_ids:
                raise ValidationError(_("The default pricelist must be included in the available pricelists."))            
            for pm in config.payment_method_ids:
                if pm.journal_id and pm.journal_id.currency_id and pm.journal_id.currency_id != config.currency_id:
                    raise ValidationError(_("All payment methods must be in the same currency as the Sales Journal or the company currency if that is not set."))            
            if config.invoice_journal_id.currency_id and config.invoice_journal_id.currency_id != config.currency_id:
                raise ValidationError(_("The invoice journal must be in the same currency as the Sales Journal or the company currency if that is not set."))            