# -*- coding: utf-8 -*-

from odoo import _, api, models
from odoo.exceptions import ValidationError

from odoo.addons.website.models.website import slugify

# SEO URL Model
class SEOURL(models.AbstractModel):
    _name = "website_seo_url"
    _description = "Website SEO URL"

    _seo_url_field = "seo_url"

    # Same Value SEO URL Name Convert Functionality
    @api.model
    def _check_seo_url(self, vals, record_id=0):
        field = self._seo_url_field
        vals = vals or {}
        value = vals.get(field)
        if value:
            original_value = slugify(value)
            counter = 0
            while True:
                new_value = "{}-{}".format(original_value, counter) if counter > 0 else original_value
                res = self.search([(field, "=", new_value), ("id", "!=", record_id)])
                if not res:
                    vals[field] = new_value
                    break
                counter += 1
        return vals


    @api.model
    def create(self, vals):
        vals = self._check_seo_url(vals)
        return super(SEOURL, self).create(vals)

    def write(self, vals):
        for r in self:
            vals = r._check_seo_url(vals, record_id=r.id)
            super(SEOURL, r).write(vals)
        return True

    # SEO URL Unique Value Check
    @api.constrains("_seo_url_field")
    def _check_seo_url_uniq(self):
        for r in self:
            value = getattr(
                r.with_context(lang=self.env.user.lang), self._seo_url_field
            )
            if (
                value
                and len(
                    self.with_context(lang=self.env.user.lang).search(
                        [(self._seo_url_field, "=", value)]
                    )
                )
                > 1
            ):
                raise ValidationError(
                    _(
                        "SEO URL must be unique! Auto changing name failed. Try different name."
                    )
                )
