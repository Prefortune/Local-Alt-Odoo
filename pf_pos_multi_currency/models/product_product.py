from odoo import models,fields,api


class StockLocation(models.Model):
    _inherit = "stock.location"


    pf_stock_altration=fields.Boolean(string="Altration Location")

class MrpProduction(models.Model):
    _inherit="mrp.production"

