from odoo import api, fields, models
from lxml import etree
import logging
from types import SimpleNamespace
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)

class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    select_template_experience = fields.Selection([
        ('blue_gold', 'Blue And Gold Template'),
        ('gray_gold', 'Gray And Gold Template'),
        ('red_gold', 'Red And Gold Template'),
        ('green', 'Green Template'),
        ('black_gray', 'Black And Gray Template'),
        ('gold', 'Gold Template'),
        ('blue_white', 'Blue And White Template'),
        ('darkblue_white', 'Dark Blue And White Template'),
        ('gold_purple', 'Gold And Purple Template'),
        ('gold_blue', 'Gold And Blue Design Template'),
    ], string="Experience Template", config_parameter="pf_generate_employee_experience_relieving_letter.select_template_experience", default="blue_gold")

    select_template_relieving = fields.Selection([
        ('blue_gold', 'Blue And Gold Template'),
        ('gray_gold', 'Gray And Gold Template'),
        ('red_gold', 'Red And Gold Template'),
        ('green', 'Green Template'),
        ('black_gray', 'Black And Gray Template'),
        ('gold', 'Gold Template'),
        ('blue_white', 'Blue And White Template'),
        ('darkblue_white', 'Dark Blue And White Template'),
        ('gold_purple', 'Gold And Purple Template'),
        ('gold_blue', 'Gold And Blue Design Template'),
    ], string="Relieving Template", config_parameter="pf_generate_employee_experience_relieving_letter.select_template_relieving", default="blue_gold")

    template_code_experience = fields.Text(string="Experience Template Code")
    template_code_relieving = fields.Text(string="Relieving Template Code")
    image_url_experience = fields.Char(string="Experience Background Image URL", compute='_compute_image_url', store=True)
    image_url_relieving = fields.Char(string="Relieving Background Image URL", compute='_compute_image_url', store=True)

    template_preview_experience = fields.Html(string="Experience Template Preview", compute="_compute_template_preview")
    template_preview_relieving = fields.Html(string="Relieving Template Preview", compute="_compute_template_preview")

    @api.depends('template_code_experience', 'template_code_relieving')
    def _compute_template_preview(self):
        for record in self:
            # Helper function to render preview for a given template code
            def render_preview(template_code, certificate_type, image_url):
                if template_code:
                    try:
                        template_code = template_code.strip()
                        if '<t t-name="' not in template_code:
                            template_code = f'<t t-name="dummy_preview_{certificate_type}">{template_code}</t>'

                        # Create an ir.ui.view in memory
                        view = self.env['ir.ui.view'].create({
                            'arch': template_code,
                            'type': 'qweb',
                            'name': f'dynamic_preview_template_{certificate_type}',
                        })

                        # Create mock objects to simulate Odoo records
                        mock_job = SimpleNamespace(name='Software Engineer')
                        mock_employee = SimpleNamespace(name='John Doe', job_id=mock_job)
                        mock_company = SimpleNamespace(name='Your Company Name')

                        # Render the template with mock objects
                        result = self.env['ir.qweb']._render(view.id, values={
                            'employee': mock_employee,
                            'company': mock_company,
                            'joining_date': '01-01-2015',
                            'ending_date': '20-12-2020',
                            'current_date': fields.Date.today().strftime('%d-%m-%Y'),
                            'background_url': image_url,
                        })

                        rendered_html = result.decode('utf-8') if isinstance(result, bytes) else result
                        _logger.info("Rendered %s Preview: %s", certificate_type.capitalize(), rendered_html)
                        return rendered_html
                    except Exception as e:
                        _logger.error("Error rendering %s preview: %s", certificate_type, str(e))
                        return f"<p style='color:red;'>Error rendering {certificate_type} preview: {str(e)}</p>"
                return f"<p style='color:gray;'>No {certificate_type} template code provided.</p>"

            # Compute previews for both certificate types
            record.template_preview_experience = render_preview(record.template_code_experience, 'experience', record.image_url_experience)
            record.template_preview_relieving = render_preview(record.template_code_relieving, 'relieving', record.image_url_relieving)

    @api.depends('select_template_experience', 'select_template_relieving')
    def _compute_image_url(self):
        for record in self:
            template_image_mapping = {
                'blue_gold': '/pf_generate_employee_experience_relieving_letter/static/src/img/blue_and_gold.png',
                'gray_gold': '/pf_generate_employee_experience_relieving_letter/static/src/img/gray_and_gold.png',
                'red_gold': '/pf_generate_employee_experience_relieving_letter/static/src/img/red.png',
                'green': '/pf_generate_employee_experience_relieving_letter/static/src/img/green.png',
                'black_gray': '/pf_generate_employee_experience_relieving_letter/static/src/img/black_and_gray.png',
                'gold': '/pf_generate_employee_experience_relieving_letter/static/src/img/golden.png',
                'blue_white': '/pf_generate_employee_experience_relieving_letter/static/src/img/blue_and_white.png',
                'darkblue_white': '/pf_generate_employee_experience_relieving_letter/static/src/img/dark_blue_and_white.png',
                'gold_purple': '/pf_generate_employee_experience_relieving_letter/static/src/img/purple.png',
                'gold_blue': '/pf_generate_employee_experience_relieving_letter/static/src/img/gold_and_blue.png',
            }
            # Compute separate image URLs for Experience and Relieving
            record.image_url_experience = template_image_mapping.get(record.select_template_experience, '')
            record.image_url_relieving = template_image_mapping.get(record.select_template_relieving, '')

    @api.onchange('select_template_experience', 'select_template_relieving')
    def _onchange_select_template(self):
        self.ensure_one()
        # Load Experience template
        if self.select_template_experience:
            experience_template = self.env['ir.ui.view'].sudo().search([
                ('key', '=', f'pf_generate_employee_experience_relieving_letter.{self.select_template_experience}_experience_template')
            ], limit=1)
            if experience_template:
                template_xml = etree.fromstring(experience_template.arch)
                background_url_element = template_xml.xpath("//t[@t-set='background_url']")
                if background_url_element:
                    self.image_url_experience = background_url_element[0].get('t-value').split("'")[-2]
                else:
                    self.image_url_experience = f"/pf_generate_employee_experience_relieving_letter/static/src/img/{self.select_template_experience}.png"
                self.template_code_experience = etree.tostring(template_xml, encoding='unicode', pretty_print=True)
            else:
                self.template_code_experience = ''
                self.image_url_experience = ''
        else:
            self.template_code_experience = ''
            self.image_url_experience = ''

        # Load Relieving template
        if self.select_template_relieving:
            relieving_template = self.env['ir.ui.view'].sudo().search([
                ('key', '=', f'pf_generate_employee_experience_relieving_letter.{self.select_template_relieving}_relieving_template')
            ], limit=1)
            if relieving_template:
                template_xml = etree.fromstring(relieving_template.arch)
                background_url_element = template_xml.xpath("//t[@t-set='background_url']")
                if background_url_element:
                    self.image_url_relieving = background_url_element[0].get('t-value').split("'")[-2]
                else:
                    self.image_url_relieving = f"/pf_generate_employee_experience_relieving_letter/static/src/img/{self.select_template_relieving}.png"
                self.template_code_relieving = etree.tostring(template_xml, encoding='unicode', pretty_print=True)
            else:
                self.template_code_relieving = ''
                self.image_url_relieving = ''
        else:
            self.template_code_relieving = ''
            self.image_url_relieving = ''

    @api.onchange('template_code_experience', 'template_code_relieving')
    def _onchange_template_code(self):
        # Ensure the image URL is properly included when template code is edited
        for template_code, field_name, image_url in [
            (self.template_code_experience, 'template_code_experience', self.image_url_experience),
            (self.template_code_relieving, 'template_code_relieving', self.image_url_relieving)
        ]:
            if template_code and image_url:
                try:
                    template_xml = etree.fromstring(template_code)
                    background_url_element = template_xml.xpath("//t[@t-set='background_url']")
                    if not background_url_element:
                        background_url = f"request.env['ir.config_parameter'].sudo().get_param('web.base.url') + '{image_url}'"
                        t_set_element = etree.Element("t", {"t-set": "background_url", "t-value": background_url})
                        template_xml.insert(0, t_set_element)
                    self[field_name] = etree.tostring(template_xml, encoding='unicode', pretty_print=True)
                except Exception as e:
                    _logger.error("Error processing %s: %s", field_name, str(e))

    def set_values(self):
        # Save the template codes back to the corresponding view records
        for template_key, template_code, select_template, image_url in [
            (f'{self.select_template_experience}_experience_template', self.template_code_experience, self.select_template_experience, self.image_url_experience),
            (f'{self.select_template_relieving}_relieving_template', self.template_code_relieving, self.select_template_relieving, self.image_url_relieving)
        ]:
            if not select_template:
                continue  # Skip if no template is selected
            template = self.env['ir.ui.view'].sudo().search([
                ('key', '=', f'pf_generate_employee_experience_relieving_letter.{template_key}')
            ], limit=1)

            if template and template_code:
                try:
                    template_xml = etree.fromstring(template_code)
                    background_url = f"request.env['ir.config_parameter'].sudo().get_param('web.base.url') + '{image_url}'"
                    background_url_element = template_xml.xpath("//t[@t-set='background_url']")
                    if background_url_element:
                        background_url_element[0].set("t-value", background_url)
                    else:
                        t_set_element = etree.Element("t", {"t-set": "background_url", "t-value": background_url})
                        template_xml.insert(0, t_set_element)
                    template.write({
                        'arch': etree.tostring(template_xml, encoding='unicode', pretty_print=True)
                    })
                except Exception as e:
                    _logger.error("Error saving template %s: %s", template_key, str(e))

        return super().set_values()

    @api.constrains('template_code_experience', 'template_code_relieving')
    def _template_code_length(self):
        for record in self:
            for field in ['template_code_experience', 'template_code_relieving']:
                if record[field] and len(record[field]) > 4000:
                    raise ValidationError(f"The {field.replace('_', ' ')} is too long. Please limit it to 5000 characters.")



# from odoo import api, fields, models
# from lxml import etree
# import logging
# from types import SimpleNamespace
# from odoo.exceptions import ValidationError

# _logger = logging.getLogger(__name__)

# class ResConfigSettings(models.TransientModel):
#     _inherit = "res.config.settings"

#     select_template = fields.Selection([
#         ('blue_gold', 'Blue And Gold Template'),
#         ('gray_gold', 'Gray And Gold Template'),
#         ('red_gold', 'Red And Gold Template'),
#         ('green', 'Green Template'),
#         ('black_gray', 'Black And Gray Template'),
#         ('gold', 'Gold Template'),
#         ('blue_white', 'Blue And White Template'),
#         ('darkblue_white', 'Dark Blue And White Template'),
#         ('gold_purple', 'Gold And Purple Template'),
#         ('gold_blue', 'Gold And Blue Design Template'),
#     ], string="Select Template", config_parameter="pf_generate_employee_experience_relieving_letter.select_template", default="blue_gold")

#     template_code = fields.Text(string="Template Code")
#     image_url = fields.Char(string="Background Image URL", compute='_compute_image_url', store=True)

#     template_preview= fields.Html(string="Template Preview",compute="_compute_template_preview")




#     @api.depends('template_code')
#     def _compute_template_preview(self):
#         for record in self:
#             if record.template_code:
#                 try:
#                     template_code = record.template_code.strip()
#                     if '<t t-name="' not in template_code:
#                         template_code = f'<t t-name="dummy_preview">{template_code}</t>'

#                     # Create an ir.ui.view in memory
#                     view = self.env['ir.ui.view'].create({
#                         'arch': template_code,
#                         'type': 'qweb',
#                         'name': 'dynamic_preview_template',
#                     })

#                     # Create mock objects to simulate Odoo records
#                     mock_job = SimpleNamespace(name='Software Engineer')
#                     mock_employee = SimpleNamespace(name='John Doe', job_id=mock_job)
#                     mock_company = SimpleNamespace(name='Your Company Name')

#                     # Render the template with mock objects
#                     result = self.env['ir.qweb']._render(view.id, values={
#                         'employee': mock_employee,
#                         'company': mock_company,
#                         'joining_date': '01-01-20015',
#                         'ending_date': '20-12-2020',
#                         'current_date': fields.Date.today().strftime('%d-%m-%Y'),
#                         'certificate_type': 'experience',  # Or 'relieving' for testing
#                         'background_url': record.image_url,
#                     })

#                     rendered_html = result.decode('utf-8') if isinstance(result, bytes) else result
#                     _logger.info("Rendered Preview: %s", rendered_html)
#                     record.template_preview = rendered_html
#                 except Exception as e:
#                     _logger.error("Error rendering preview: %s", str(e))
#                     record.template_preview = f"<p style='color:red;'>Error rendering preview: {str(e)}</p>"
#             else:
#                 record.template_preview = "<p style='color:gray;'>No template code provided.</p>"


#     @api.depends('select_template')
#     def _compute_image_url(self):
#         for record in self:
#             # Dynamically set image URL based on template
#             template_image_mapping = {
#                 'blue_gold': '/pf_generate_employee_experience_relieving_letter/static/src/img/blue_and_gold.png',
#                 'gray_gold': '/pf_generate_employee_experience_relieving_letter/static/src/img/gray_and_gold.png',
#                 'red_gold': '/pf_generate_employee_experience_relieving_letter/static/src/img/red.png',
#                 'green': '/pf_generate_employee_experience_relieving_letter/static/src/img/green.png',
#                 'black_gray': '/pf_generate_employee_experience_relieving_letter/static/src/img/black_and_gray.png',
#                 'gold': '/pf_generate_employee_experience_relieving_letter/static/src/img/golden.png',
#                 'blue_white': '/pf_generate_employee_experience_relieving_letter/static/src/img/blue_and_white.png',
#                 'darkblue_white': '/pf_generate_employee_experience_relieving_letter/static/src/img/dark_blue_and_white.png',
#                 'gold_purple': '/pf_generate_employee_experience_relieving_letter/static/src/img/purple.png',
#                 'gold_blue': '/pf_generate_employee_experience_relieving_letter/static/src/img/gold_and_blue.png',
#             }
#             self.image_url = template_image_mapping.get(record.select_template, '')

#     @api.onchange('select_template')
#     def _onchange_select_template(self):
#         self.ensure_one()
#         if self.select_template:
#             template = self.env['ir.ui.view'].sudo().search([
#                 ('key', '=', f'pf_generate_employee_experience_relieving_letter.{self.select_template}_template')
#             ], limit=1)
#             if template:
#                 # Parse the template XML
#                 template_xml = etree.fromstring(template.arch)

#                 # Find the background URL and extract it
#                 background_url_element = template_xml.xpath("//t[@t-set='background_url']")
#                 if background_url_element:
#                     self.image_url = background_url_element[0].text
#                 else:
#                     self.image_url = f"/pf_generate_employee_experience_relieving_letter/static/src/img/{self.select_template}.png"

#                 # Modify the template code and preserve the image
#                 self.template_code = etree.tostring(template_xml, encoding='unicode', pretty_print=True)
#             else:
#                 self.template_code = ''
#                 self.image_url = ''
#         else:
#             self.template_code = ''
#             self.image_url = ''

#     @api.onchange('template_code')
#     def _onchange_template_code(self):
#         # Ensure the image URL is properly included when template code is edited
#         if self.image_url:
#             # Parse the template code
#             template_xml = etree.fromstring(self.template_code)

#             # Find if the background URL is already in the template code
#             background_url_element = template_xml.xpath("//t[@t-set='background_url']")
#             if not background_url_element:
#                 # Add background_url if it's missing
#                 background_url = f"request.env['ir.config_parameter'].sudo().get_param('web.base.url') + '{self.image_url}'"
#                 t_set_element = etree.Element("t", {"t-set": "background_url", "t-value": background_url})
#                 template_xml.insert(0, t_set_element)

#             # Convert back to string and save it
#             self.template_code = etree.tostring(template_xml, encoding='unicode', pretty_print=True)

#     def set_values(self):
#         # Save the template code back to the corresponding view record
#         template = self.env['ir.ui.view'].sudo().search([
#             ('key', '=', f'pf_generate_employee_experience_relieving_letter.{self.select_template}_template')
#         ], limit=1)

#         if template:
#             # Parse the template code
#             template_xml = etree.fromstring(self.template_code)

#             # Ensure the background_url is inserted properly
#             background_url = f"request.env['ir.config_parameter'].sudo().get_param('web.base.url') + '{self.image_url}'"
#             background_url_element = template_xml.xpath("//t[@t-set='background_url']")

#             if background_url_element:
#                 background_url_element[0].set("t-value", background_url)
#             else:
#                 # If background_url doesn't exist, create it
#                 t_set_element = etree.Element("t", {"t-set": "background_url", "t-value": background_url})
#                 template_xml.insert(0, t_set_element)

#             # Save the modified template back to the view record
#             template.write({
#                 'arch': etree.tostring(template_xml, encoding='unicode', pretty_print=True)
#             })

#         return super().set_values()





#     @api.constrains('template_code')
#     def _template_code_length(self):
#         for record in self:
#             if record.template_code and len(record.template_code) > 5000: 
# 	            raise ValidationError("The text is too long. Please limit it to 5000 characters.")






