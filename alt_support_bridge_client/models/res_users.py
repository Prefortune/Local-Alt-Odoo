from odoo import models, fields, api

class ResUsers(models.Model):
    _inherit = 'res.users'

    support_channel_access = fields.Selection([
        ('none', 'No Access'),
        ('shared', 'Shared Channel Only'),
        ('both', 'Both Shared and Personal Channels')
    ], string='Support Channel Access', default='none', required=True)

    @api.model
    def create(self, vals):
        user = super(ResUsers, self).create(vals)
        if user.support_channel_access != 'none':
            self._create_support_channels(user)
        return user

    def write(self, vals):
        if 'support_channel_access' in vals:
            old_access = self.support_channel_access
            result = super(ResUsers, self).write(vals)
            if vals['support_channel_access'] != old_access:
                self._update_support_channels()
            return result
        return super(ResUsers, self).write(vals)

    def _create_support_channels(self, user):
        """Create support channels for the user based on their access level."""
        company = user.company_id
        if user.support_channel_access in ['shared', 'both']:
            self._create_shared_channel(company)
        if user.support_channel_access == 'both':
            self._create_personal_channel(user, company)

    def _create_shared_channel(self, company):
        """Create or get the shared channel (global, not per company)."""
        channel_name = f'alt support - {company.name}'
        channel = self.env['discuss.channel'].search([
            ('name', '=', channel_name)
        ], limit=1)
        
        if not channel:
            channel = self.env['discuss.channel'].create({
                'name': channel_name,
                'channel_type': 'channel',
            })
        return channel

    def _create_personal_channel(self, user, company):
        """Create or get the personal channel for the user (global, not per company)."""
        channel_name = f'alt support - {company.name} - {user.name}'
        channel = self.env['discuss.channel'].search([
            ('name', '=', channel_name)
        ], limit=1)
        
        if not channel:
            channel = self.env['discuss.channel'].create({
                'name': channel_name,
                'channel_type': 'channel',
            })
        return channel

    def _update_support_channels(self):
        """Update support channels based on new access level (global, not per company)."""
        for user in self:
            company = user.company_id
            if user.support_channel_access == 'none':
                # Remove user from all support channels
                channels = self.env['discuss.channel'].search([
                    ('name', 'like', f'alt support - {company.name}')
                ])
                channels.write({'channel_partner_ids': [(3, user.partner_id.id)]})
            else:
                self._create_support_channels(user) 