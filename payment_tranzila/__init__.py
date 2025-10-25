# -*- coding: utf-8 -*-

from . import controllers
from . import models
from odoo.addons.payment import reset_payment_provider


def uninstall_hook(env):
    reset_payment_provider(env, 'tranzila')
