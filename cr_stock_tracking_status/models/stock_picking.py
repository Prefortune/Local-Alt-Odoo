from odoo import models, fields,api,_

class StockPicking(models.Model):
    _inherit = 'stock.picking'

    tracking_status = fields.Selection([
        ('none', 'None'),
        ('uploaded', 'העמס'),
        ('drive', 'התחל נהיגה'),
        ('downloaded', 'פרוק סחורה'),
        ('done', 'סיים וחתום'),
    ], string="Tracking Status", default='none', tracking=True)


    def change_tracking_status(self):
        status_order = ['none', 'uploaded', 'drive', 'downloaded', 'done']
        updated = False

        for picking in self:
            current = picking.tracking_status or 'none'
            try:
                index = status_order.index(current)
                if index < len(status_order) - 1:
                    picking.tracking_status = status_order[index + 1]
                    updated = True
            except ValueError:
                picking.tracking_status = 'uploaded'
                updated = True

        return updated

    def can_show_signature_modal(self):
        """Returns True if tracking_status is 'downloaded' or 'done' and is_signed is False."""
        self.ensure_one()
        return self.tracking_status == 'done' and not self.is_signed

class StockQuantPackage(models.Model):
    _inherit = 'stock.quant.package'

    load_status = fields.Selection([
        ('none', 'None'),
        ('loaded', 'Loaded'),
        ('downloaded', 'Downloaded'),
    ], string="Load Status", default='none', tracking=True)

    def _should_unpack(self, vals):
        """Determine if package should be unpacked."""
        load_status = vals.get('load_status')
        location_id = vals.get('location_id')

 
        for package in self:
            new_status = load_status or package.load_status
            new_location = self.env['stock.location'].browse(location_id) if location_id else package.location_id

            is_consignation = False
            loc = new_location
            while loc:
                if loc.consignation_locations:
                    is_consignation = True
                    break
                loc = loc.location_id

            if is_consignation and new_status == 'downloaded':
                if package.quant_ids:
                    package.unpack()


    def write(self, vals):
        # Call unpack logic before actually writing
        self._should_unpack(vals)
        return super(StockQuantPackage, self).write(vals)