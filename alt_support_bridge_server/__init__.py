from . import models
from . import controllers

def _post_init_hook(cr, registry):
    """Post-init hook to ensure proper module initialization."""
    from odoo import api, SUPERUSER_ID
    env = api.Environment(cr, SUPERUSER_ID, {})
    env['discuss.channel']._update_alt_support_channels() 