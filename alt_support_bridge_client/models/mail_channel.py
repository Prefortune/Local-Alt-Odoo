from odoo import models, fields, api

class DiscussChannel(models.Model):
    _inherit = 'discuss.channel'

    @api.model
    def _create_alt_support_channels(self, company):
        """Create Alt Support channels for a company."""
        # Create shared channel
        shared_channel_name = f"alt support - {company.name}"
        shared_channel = self.search([('name', '=', shared_channel_name)], limit=1)
        if not shared_channel:
            shared_channel = self.create({
                'name': shared_channel_name,
                'channel_type': 'channel',
                'public': 'private',
            })

        # Create personal channels for users with access
        users = self.env['res.users'].search([
            ('company_id', '=', company.id),
            ('support_channel_access', 'in', ['both', 'personal'])
        ])
        
        for user in users:
            personal_channel_name = f"alt support - {company.name} - {user.name}"
            personal_channel = self.search([('name', '=', personal_channel_name)], limit=1)
            if not personal_channel:
                personal_channel = self.create({
                    'name': personal_channel_name,
                    'channel_type': 'channel',
                    'public': 'private',
                })
                # Add the user to the channel
                personal_channel.write({
                    'channel_partner_ids': [(4, user.partner_id.id)]
                })

        return shared_channel

    @api.model
    def _update_alt_support_channels(self):
        """Update Alt Support channels for all companies."""
        companies = self.env['res.company'].search([])
        for company in companies:
            self._create_alt_support_channels(company) 