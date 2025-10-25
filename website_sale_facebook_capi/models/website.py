from odoo import models


class Website(models.Model):
    _inherit = "website"

    def _tracking_run_script(self, service, product_data, order, event_type):
        """ Do not run the JS script method to a send data to FB,
            if the CAPI mode and the "Remove FB Pixel" option are activated.
        """
        self.ensure_one()
        if service.is_fb_capi() and service.api_deactivate_pixel:
            return False
        return super(Website, self)._tracking_run_script(service, product_data, order, event_type)

    def _fbp_allowed_services(self):
        services = super(Website, self)._fbp_allowed_services()
        return services.filtered(
            lambda s: not s.api_is_active or s.api_is_active and not s.api_deactivate_pixel
        )
