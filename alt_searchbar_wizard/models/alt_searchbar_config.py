from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
import logging
_logger = logging.getLogger(__name__)

class AltSearchbarConfig(models.Model):
    _name = 'alt.searchbar.config'
    _description = 'Alt Searchbar Configuration'
    _rec_name = 'name'

    name = fields.Char(
        string='Name',
        required=True,
        help='Internal name for this configuration'
    )
    
    website_id = fields.Many2one(
        'website',
        string='Website',
        required=True,
        ondelete='cascade',
        help='Website this configuration belongs to'
    )
    
    category_ids = fields.Many2many(
        'product.public.category',
        string='Categories',
        help='Product categories to include in search'
    )
    
    attribute_ids = fields.Many2many(
        'product.attribute',
        string='Attributes',
        help='Product attributes to include in search'
    )
    
    tag_ids = fields.Many2many(
        'product.tag',
        string='Tags',
        help='Product tags to include in search'
    )
    
    show_price_filter = fields.Boolean(
        string='Show Price Filter',
        default=True,
        help='Show price range filter in searchbar'
    )
    
    is_active = fields.Boolean(
        string='Active',
        default=True,
        help='Whether this configuration is active'
    )
    
    show_on_all_pages = fields.Boolean(
        string='Show on All Pages',
        default=True,
        help='Whether to show searchbar on all pages by default'
    )

    @api.constrains('website_id')
    def _check_website_unique(self):
        """Ensure only one active configuration per website"""
        for record in self:
            if record.is_active:
                existing = self.search([
                    ('website_id', '=', record.website_id.id),
                    ('is_active', '=', True),
                    ('id', '!=', record.id)
                ])
                if existing:
                    raise ValidationError(_('Only one active configuration allowed per website.'))

    @api.model
    def create(self, vals):
        """Automatically assign current website if not specified"""
        if not vals.get('website_id'):
            website = self.env['website'].get_current_website()
            if website:
                vals['website_id'] = website.id
        return super().create(vals)

    def get_active_config(self, website_id):
        """Get active configuration for given website"""
        return self.search([
            ('website_id', '=', website_id),
            ('is_active', '=', True)
        ], limit=1)

    def get_categories_data(self):
        """Get categories data for frontend"""
        categories = []
        for category in self.category_ids:
            categories.append([category.id, category.name])
        return categories

    def get_attributes_data(self):
        """Get attributes data for frontend"""
        attributes = []
        for attr in self.attribute_ids:
            values = []
            for value in attr.value_ids:
                values.append([value.id, value.name])
            attributes.append([attr.id, attr.name, values])
        return attributes

    def get_tags_data(self):
        """Get tags data for frontend"""
        tags = []
        for tag in self.tag_ids:
            _logger.info("tags -------------------- %s",tag.name)
            tags.append([tag.id, tag.name])
        return tags

    def get_price_ranges(self):
        """Get price ranges for frontend"""
        ranges = [
            {'min': 0, 'max': 1000, 'label': '₪ 0 עד ₪ 1,000'},
            {'min': 1000, 'max': 2000, 'label': '₪ 1,000 עד ₪ 2,000'},
            {'min': 2000, 'max': 4000, 'label': '₪ 2,000 עד ₪ 4,000'},
            {'min': 4000, 'max': 6000, 'label': '₪ 4,000 עד ₪ 6,000'},
            {'min': 6000, 'max': 8000, 'label': '₪ 6,000 עד ₪ 8,000'},
            {'min': 8000, 'max': 10000, 'label': '₪ 8,000 עד ₪ 10,000'},
            {'min': 10000, 'max': 15000, 'label': '₪ 10,000 עד ₪ 15,000'},
            {'min': 15000, 'max': 20000, 'label': '₪ 15,000 עד ₪ 20,000'},
            {'min': 20000, 'max': 50000, 'label': '₪ 20,000 ומעלה'},
        ]
        return ranges 