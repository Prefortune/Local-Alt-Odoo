# -*- coding: utf-8 -*-

from odoo import _, api, models
from odoo.exceptions import ValidationError
import re

# SEO URL Model


class SEOURL(models.AbstractModel):
    _name = "website_seo_url"
    _description = "Website SEO URL"

    _seo_url_field = "seo_url"

    _seo_url_field_lang = "seo_url_language"

    # Same Value SEO URL Name Convert Functionality
    def _check_seo_url(self, vals, record_id=0):
        field = self._seo_url_field
        vals = vals or {}
        value = vals.get(field)
        self._check_url_field_lang(vals)
        if value:
            original_value = self.env['ir.http']._slugify_one(
                value, max_length=0, field_name='seo_url')
            counter = 0
            while True:
                new_value = "{}-{}".format(original_value,
                                           counter) if counter > 0 else original_value
                res = self.search(
                    [(field, "=", new_value), ("id", "!=", record_id)])
                if not res:
                    vals[field] = new_value
                    break
                counter += 1
        return vals

    def create(self, vals):
        vals = self._check_seo_url(vals)
        return super(SEOURL, self).create(vals)

    def write(self, vals):
        for r in self:
            vals = r._check_seo_url(vals, record_id=r.id)
            super(SEOURL, r).write(vals)
        return True

    # SEO URL Unique Value Check
    @api.constrains("seo_url")
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

    def _check_url_field_lang(self, vals):
        """
        Validates that the URL field contains only characters allowed by the selected language.
        """
        field_lang = vals.get(
            self._seo_url_field_lang) or self.seo_url_language
        field_url = vals.get(self._seo_url_field) or self.seo_url
        patterns = {
            'english': r'^[a-zA-Z0-9-_:/?=&]+$',
            'arabic': r'^[\u0600-\u06FF0-9\-_:\/\?=&\s]+$',
            'hebrew': r'^[\u0590-\u05FF0-9\-_:\/?=&\s]+$',
        }

        pattern = patterns.get(field_lang)

        if field_url and pattern and not re.match(pattern, field_url):
            raise models.ValidationError(
                f"The URL can only contain characters valid for the selected language ({field_lang})."
            )
