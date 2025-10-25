# -*- coding: utf-8 -*-

from odoo import api, models
from odoo.http import request
from odoo.addons.base.models.ir_http import RequestUID
import re
import unicodedata
# optional python-slugify import (https://github.com/un33k/python-slugify)
try:
    import slugify as slugify_lib
except ImportError:
    slugify_lib = None
from odoo.addons.base.models import ir_http
import werkzeug.exceptions

ALLOWED_MODULES = ['product.template', 'product.public.category']
_UNSLUG_RE = re.compile(
    r'(?:(\w{1,2}|\w[A-Za-z0-9-_]+?\w)-)?(-?\d+)(?=$|\/|#|\?)')  # ORIGINAL
_MILTI_LANG_SLUG_RE = r"(?:(\w{1,2}|\w[A-Za-z0-9-_\\u0590-\\u05FF\\u0600-\\u06FF]+?))(?=$|\\/|#|\\?)"


# Model Converter Custom Class Method
class ModelConverter(ir_http.ModelConverter):
    def __init__(self, url_map, model=False, domain="[]"):
        super(ModelConverter, self).__init__(url_map, model)
        self.regex = _MILTI_LANG_SLUG_RE

    def to_python(self, value) -> models.BaseModel:
        _uid = RequestUID(value=value, converter=self)
        env = api.Environment(request.cr, _uid, request.context)
        record_id = None
        field = getattr(request.registry[self.model], "_seo_url_field", None)
        if field and field in request.registry[self.model]._fields:
            cur_lang = (request.context or {}).get("lang", "en_US")
            cur_lang_active = env["res.lang"].sudo().search(
                [("code", "=", cur_lang), ("active", "=", True)], limit=1)
            langs = [cur_lang] if cur_lang_active else [] + [
                lang
                for lang, _ in env["res.lang"].sudo().get_installed()
                if lang != cur_lang
            ]
            for lang in langs:
                res = (
                    env[self.model]
                    .with_context(lang=lang)
                    .sudo()
                    .search([(field, "=", value)])
                )
                if res:
                    record_id = res[0].id
                    break

        if record_id:
            return env[self.model].with_context(_converter_value=value).browse(record_id)

        # fallback to original implementation
        original_value = _UNSLUG_RE.match(value)
        if not original_value:
            raise werkzeug.exceptions.NotFound()
        self.regex = _UNSLUG_RE.pattern
        return super().to_python(value)

# Custom Class Method Converter Added


class IrHttp(models.AbstractModel):
    _inherit = "ir.http"

    @classmethod
    def _get_converters(cls) -> dict[str, type]:
        """ Get the converters list for custom url pattern werkzeug need to
            match Rule. This override adds the website ones.
        """
        return dict(
            super(IrHttp, cls)._get_converters(),
            model=ModelConverter,
        )

    # Default Slug Functionality Override
    @classmethod
    def _slug(cls, value: models.BaseModel | tuple[int, str]) -> str:
        field = getattr(value, "_seo_url_field", None)
        if field and isinstance(value, models.BaseModel) and hasattr(value, field):
            name = getattr(value, field, None)
            if name:
                return name
        return super()._slug(value)

    @classmethod
    def _slugify_one(cls, value: str, max_length: int = 0, field_name: str = None) -> str:
        """
        Transform a string to a slug that can be used in a URL path.
        Supports Hebrew and Arabic without transliteration.
        """
        lang = 'english'  # default fallback

        # Try to determine language from target record
        target_record = cls._get_traget_record(value)
        if hasattr(target_record, 'seo_url_language'):
            lang = getattr(target_record, 'seo_url_language', 'english')

        # Normalize input
        uni = unicodedata.normalize('NFKC', value)

        if lang == 'hebrew':
            uni = unicodedata.normalize('NFKC', value)
            slug_str = re.sub(r'[^\u0590-\u05FF0-9\- ]',
                              '', uni).strip().lower()
            slug_str = re.sub(r'\s+', '-', slug_str)  # רווחים → מקפים
            slug_str = re.sub(r'-+', '-', slug_str)   # מקפים רצופים
            slug_str = slug_str.strip('-')            # מקף בתחילת/סוף
            print(f"[DEBUG] slug_str after hebrew clean: {slug_str}")
            return slug_str[:max_length] if max_length > 0 else slug_str

        elif lang == 'arabic':
            slug_str = re.sub(r'[^\w\u0600-\u06FF\- ]',
                              '', uni).strip().lower()
        else:
            # fallback to ASCII slug
            slug_str = unicodedata.normalize('NFKD', uni)
            slug_str = slug_str.encode('ascii', 'ignore').decode('ascii')
            slug_str = re.sub(r'[^\w\- ]', '', slug_str).strip().lower()

        slug_str = re.sub(r'[-\s]+', '-', slug_str)
        return slug_str[:max_length] if max_length > 0 else slug_str

    @classmethod
    def _get_traget_record(cls, value: str):
        for model in ALLOWED_MODULES:
            record = request.env[model].search(
                [('display_name', '=', value)], limit=1)
            if record and record.seo_url:
                return record
        return None
