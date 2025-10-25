# -*- coding: utf-8 -*-

from odoo import models, fields, api


class alt_ad_cart(models.Model):
    _name = 'alt.ad.card'
    _order = 'create_date desc'

    name = fields.Char(string='Internal Name', required=True)

    alt_website = fields.Many2one('website',string="Select Website")
    alt_device_type = fields.Selection([('desktop','Desktop'),('mobile','Mobile'),('both','Both Mobile And Desktop')], string="This Ad For ?",default="both",required=True)
    alt_content_html = fields.Html(string='HTML Content', sanitize=False,
                                   help='Raw HTML that will be injected into the shop. Admin-only content.')
    
    alt_category_ids = fields.Many2many(
        comodel_name='product.public.category',
        relation='alt_ad_card_category_rel',
        column1='ad_id',
        column2='category_id',
        string='Target Categories',
        help='If empty, applies to all categories.'
    )
    alt_tag_ids = fields.Many2many(
        comodel_name='product.tag',
        relation='alt_ad_card_tag_rel',
        column1='ad_id',
        column2='tag_id',
        string='Target Tags',
        help='If empty, applies to all tags.'
    )
    # alt_user_group_ids = fields.Many2many(
    #     comodel_name='res.groups',
    #     relation='alt_ad_card_group_rel',
    #     column1='ad_id',
    #     column2='group_id',
    #     string='Target User Groups',
    #     help='If empty, applies to all users.'
    # )
    # alt_lang_ids = fields.Many2many(
    #     comodel_name='res.lang',
    #     relation='alt_ad_card_lang_rel',
    #     column1='ad_id',
    #     column2='lang_id',
    #     string='Target Languages',
    #     help='If empty, applies to all languages.'
    # )
    alt_position_type = fields.Selection([
        ('inline_card', 'Inline Card (grid)'),
        ('strip', 'Full-width Strip'),
    ], string='Display Type', default='inline_card', required=True)

    alt_display_every = fields.Integer(
        string='Display Every X Products',
        default=4,
        help='If set, tries to place the ad after every X products (or at least once per page).'
    )
    alt_priority = fields.Integer(string='Priority', default=10, help='Higher values displayed first')

    alt_active = fields.Boolean(string='Active', default=True)
