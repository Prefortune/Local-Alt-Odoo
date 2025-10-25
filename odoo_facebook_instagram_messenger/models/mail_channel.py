from odoo import _, api, fields, models, modules, tools, Command
import json
from collections import defaultdict
from odoo.tools.misc import DEFAULT_SERVER_DATETIME_FORMAT
from odoo.addons.mail.models.discuss.discuss_channel import Channel
from odoo.tools import html2plaintext
from markupsafe import Markup
import re
from odoo.exceptions import UserError
from odoo.addons.mail.models.discuss.discuss_channel_member import ChannelMember
from odoo.osv import expression


def _channel_info(self):
    """ Get the information header for the current channels
        :returns a list of updated channels values
        :rtype : list(dict)
    """
    if not self:
        return []
    channel_infos = []
    # sudo: discuss.channel.rtc.session - reading sessions of accessible channel is acceptable
    rtc_sessions_by_channel = self.sudo().rtc_session_ids._mail_rtc_session_format_by_channel(extra=True)
    current_partner, current_guest = self.env["res.partner"]._get_current_persona()
    self.env['discuss.channel'].flush_model()
    self.env['discuss.channel.member'].flush_model()
    # Query instead of ORM for performance reasons: "LEFT JOIN" is more
    # efficient than "id IN" for the cross-table condition between channel
    # (for channel_type) and member (for other fields).
    self.env.cr.execute("""
             SELECT discuss_channel_member.id
               FROM discuss_channel_member
          LEFT JOIN discuss_channel
                 ON discuss_channel.id = discuss_channel_member.channel_id
                AND discuss_channel.channel_type != 'channel'
              WHERE discuss_channel_member.channel_id in %(channel_ids)s
                AND (
                    discuss_channel.id IS NOT NULL
                 OR discuss_channel_member.rtc_inviting_session_id IS NOT NULL
                 OR discuss_channel_member.partner_id = %(current_partner_id)s
                 OR discuss_channel_member.guest_id = %(current_guest_id)s
                )
           ORDER BY discuss_channel_member.id ASC
    """, {'channel_ids': tuple(self.ids), 'current_partner_id': current_partner.id or None, 'current_guest_id': current_guest.id or None})
    all_needed_members = self.env['discuss.channel.member'].browse([m['id'] for m in self.env.cr.dictfetchall()])
    all_needed_members._discuss_channel_member_format()  # prefetch in batch
    members_by_channel = defaultdict(lambda: self.env['discuss.channel.member'])
    invited_members_by_channel = defaultdict(lambda: self.env['discuss.channel.member'])
    member_of_current_user_by_channel = defaultdict(lambda: self.env['discuss.channel.member'])
    for member in all_needed_members:
        members_by_channel[member.channel_id] += member
        if member.rtc_inviting_session_id:
            invited_members_by_channel[member.channel_id] += member
        if (current_partner and member.partner_id == current_partner) or (current_guest and member.guest_id == current_guest):
            member_of_current_user_by_channel[member.channel_id] = member
    for channel in self:
        # Separate WhatsApp, Facebook and Instagram Channels
        custom_channel = ''
        if channel._fields.get('whatsapp_channel'):
            if channel.whatsapp_channel:
                custom_channel += 'WpChannels'
        if channel._fields.get('instagram_channel'):
            if channel.instagram_channel:
                custom_channel += 'InstaChannels'
        if channel._fields.get('facebook_channel'):
            if channel.facebook_channel:
                custom_channel += 'FbChannels'
        if not custom_channel:
            info = {
                'avatarCacheKey': channel._get_avatar_cache_key(),
                'channel_type': channel.channel_type,
                'memberCount': channel.member_count,
                'id': channel.id,
                'name': channel.name,
                'defaultDisplayMode': channel.default_display_mode,
                'description': channel.description,
                'uuid': channel.uuid,
                'state': 'open',
                'is_editable': channel.is_editable,
                'is_minimized': False,
                'group_based_subscription': bool(channel.group_ids),
                'create_uid': channel.create_uid.id,
                'authorizedGroupFullName': channel.group_public_id.full_name,
                'allow_public_upload': channel.allow_public_upload,
                'model': "discuss.channel",
            }
        else:
            info = {
                'avatarCacheKey': channel._get_avatar_cache_key(),
                'channel_type': custom_channel,
                'memberCount': channel.member_count,
                'id': channel.id,
                'name': channel.name,
                'defaultDisplayMode': channel.default_display_mode,
                'description': channel.description,
                'uuid': channel.uuid,
                'state': 'open',
                'is_editable': channel.is_editable,
                'is_minimized': False,
                'is_whatsapp': True,
                'group_based_subscription': bool(channel.group_ids),
                'create_uid': channel.create_uid.id,
                'authorizedGroupFullName': channel.group_public_id.full_name,
                'allow_public_upload': channel.allow_public_upload,
                'model': "discuss.channel",
            }
        # find the channel member state
        if current_partner or current_guest:
            info['message_needaction_counter'] = channel.message_needaction_counter
            member = member_of_current_user_by_channel.get(channel, self.env['discuss.channel.member']).with_prefetch([m.id for m in member_of_current_user_by_channel.values()])
            if member:
                info['channelMembers'] = [('ADD', list(member._discuss_channel_member_format().values()))]
                info['state'] = member.fold_state or 'open'
                info['message_unread_counter'] = member.message_unread_counter
                info['is_minimized'] = member.is_minimized
                info['custom_notifications'] = member.custom_notifications
                info['mute_until_dt'] = member.mute_until_dt.strftime(DEFAULT_SERVER_DATETIME_FORMAT) if member.mute_until_dt else False
                info['seen_message_id'] = member.seen_message_id.id
                info['custom_channel_name'] = member.custom_channel_name
                info['is_pinned'] = member.is_pinned
                info['last_interest_dt'] = member.last_interest_dt.strftime(DEFAULT_SERVER_DATETIME_FORMAT)
                if member.rtc_inviting_session_id:
                    info['rtc_inviting_session'] = {'id': member.rtc_inviting_session_id.id}
        # add members info
        if channel.channel_type != 'channel':
            # avoid sending potentially a lot of members for big channels
            # exclude chat and other small channels from this optimization because they are
            # assumed to be smaller and it's important to know the member list for them
            info['channelMembers'] = [('ADD', list(members_by_channel[channel]._discuss_channel_member_format().values()))]
            info['seen_partners_info'] = sorted([{
                'id': cm.id,
                'partner_id' if cm.partner_id else 'guest_id': cm.partner_id.id if cm.partner_id else cm.guest_id.id,
                'fetched_message_id': cm.fetched_message_id.id,
                'seen_message_id': cm.seen_message_id.id,
            } for cm in members_by_channel[channel]],
                key=lambda p: p.get('partner_id', p.get('guest_id')))
        # add RTC sessions info
        info.update({
            'invitedMembers': [('ADD', list(invited_members_by_channel[channel]._discuss_channel_member_format(
                fields={'id': True, 'channel': {}, 'persona': {'partner': {'id', 'name', 'im_status'}, 'guest': {'id', 'name', 'im_status'}}}).values()))],
            'rtcSessions': [('ADD', rtc_sessions_by_channel.get(channel, []))],
        })
        channel_infos.append(info)
    return channel_infos

Channel._channel_info = _channel_info


class MailChannel(models.Model):
    _inherit = "discuss.channel"

    channel_type = fields.Selection(
        selection_add=[('FbChannels', 'Facebook Conversation'),
                       ('InstaChannels', 'Instagram Conversation')],
        ondelete={'FbChannels': 'cascade', 'InstaChannels': 'cascade'})

    im_provider_id = fields.Many2one('messenger.provider', string="Insta/Messenger Provider")

    instagram_channel = fields.Boolean(string="Instagram Channel")
    facebook_channel = fields.Boolean(string="Facebook Channel")

    def add_members(self, partner_ids=None, guest_ids=None, invite_to_rtc_call=False, open_chat_window=False, post_joined_message=True):
        """ Adds the given partner_ids and guest_ids as member of self channels. """
        current_partner, current_guest = self.env["res.partner"]._get_current_persona()
        partners = self.env['res.partner'].browse(partner_ids or []).exists()
        guests = self.env['mail.guest'].browse(guest_ids or []).exists()
        notifications = []
        all_new_members = self.env["discuss.channel.member"]
        for channel in self:
            members_to_create = []
            existing_members = self.env['discuss.channel.member'].search(expression.AND([
                [('channel_id', '=', channel.id)],
                expression.OR([
                    [('partner_id', 'in', partners.ids)],
                    [('guest_id', 'in', guests.ids)]
                ])
            ]))
            members_to_create += [{
                'partner_id': partner.id,
                'channel_id': channel.id,
            } for partner in partners - existing_members.partner_id]
            members_to_create += [{
                'guest_id': guest.id,
                'channel_id': channel.id,
            } for guest in guests - existing_members.guest_id]
            new_members = self.env['discuss.channel.member'].create(members_to_create)
            all_new_members += new_members
            for member in new_members.filtered(lambda member: member.partner_id):
                # notify invited members through the bus
                user = member.partner_id.user_ids[0] if member.partner_id.user_ids else self.env['res.users']
                if user:
                    notifications.append((member.partner_id, 'discuss.channel/joined', {
                        'channel': member.channel_id.with_user(user).with_context(allowed_company_ids=user.company_ids.ids)._channel_info()[0],
                        'invited_by_user_id': self.env.user.id,
                        'open_chat_window': open_chat_window,
                    }))
                if post_joined_message and not ((channel._fields.get('whatsapp_channel') and channel.whatsapp_channel) or (channel._fields.get('instagram_channel') and channel.instagram_channel) or (
                        channel._fields.get('facebook_channel') and channel.facebook_channel)):
                    # notify existing members with a new message in the channel
                    if member.partner_id == self.env.user.partner_id:
                        notification = Markup('<div class="o_mail_notification">%s</div>') % _('joined the channel')
                    else:
                        notification = (Markup('<div class="o_mail_notification">%s</div>') % _("invited %s to the channel")) % member.partner_id._get_html_link()
                    member.channel_id.message_post(body=notification, message_type="notification", subtype_xmlid="mail.mt_comment")
            for member in new_members.filtered(lambda member: member.guest_id):
                if post_joined_message:
                    member.channel_id.message_post(body=Markup('<div class="o_mail_notification">%s</div>') % _('joined the channel'),
                                                   message_type="notification", subtype_xmlid="mail.mt_comment")
                guest = member.guest_id
                if guest:
                    notifications.append((guest, 'discuss.channel/joined', {
                        'channel': member.channel_id.with_context(guest=guest)._channel_info()[0],
                    }))
            notifications.append((channel, 'mail.record/insert', {
                'Thread': {
                    'channelMembers': [('ADD', list(new_members._discuss_channel_member_format().values()))],
                    'id': channel.id,
                    'memberCount': channel.member_count,
                    'model': "discuss.channel",
                }
            }))
            if existing_members and (current_partner or current_guest):
                # If the current user invited these members but they are already present, notify the current user about their existence as well.
                # In particular this fixes issues where the current user is not aware of its own member in the following case:
                # create channel from form view, and then join from discuss without refreshing the page.
                notifications.append((current_partner or current_guest, 'mail.record/insert', {
                    'Thread': {
                        'channelMembers': [('ADD', list(existing_members._discuss_channel_member_format().values()))],
                        'id': channel.id,
                        'memberCount': channel.member_count,
                        'model': "discuss.channel",
                    }
                }))
        if invite_to_rtc_call:
            for channel in self:
                current_channel_member = self.env['discuss.channel.member'].search([('channel_id', '=', channel.id), ('is_self', '=', 'True')])
                # sudo: discuss.channel.rtc.session - reading rtc sessions of current user
                if current_channel_member and current_channel_member.sudo().rtc_session_ids:
                    # sudo: discuss.channel.rtc.session - current user can invite new members in call
                    current_channel_member.sudo()._rtc_invite_members(member_ids=new_members.ids)
        self.env['bus.bus']._sendmany(notifications)
        return all_new_members

    def _action_unfollow(self, partner):
        self.message_unsubscribe(partner.ids)
        member = self.env['discuss.channel.member'].search([('channel_id', '=', self.id), ('partner_id', '=', partner.id)])
        if not member:
            return True
        channel_info = self._channel_info()[0]  # must be computed before leaving the channel (access rights)
        member.unlink()
        # side effect of unsubscribe that wasn't taken into account because
        # channel_info is called before actually unpinning the channel
        channel_info['is_pinned'] = False
        if not ((self._fields.get('whatsapp_channel') and self.whatsapp_channel) or (
                    self._fields.get('instagram_channel') and self.instagram_channel) or (
                         self._fields.get('facebook_channel') and self.facebook_channel)):
            self.env['bus.bus']._sendone(partner, 'discuss.channel/leave', channel_info)
            notification = Markup('<div class="o_mail_notification">%s</div>') % _('left the channel')
            # sudo: mail.message - post as sudo since the user just unsubscribed from the channel
            self.sudo().message_post(body=notification, subtype_xmlid="mail.mt_comment", author_id=partner.id)
        self.env['bus.bus']._sendone(self, 'mail.record/insert', {
            'Thread': {
                'channelMembers': [('DELETE', {'id': member.id})],
                'id': self.id,
                'memberCount': self.member_count,
                'model': "discuss.channel",
            }
        })

@api.model_create_multi
def create(self, vals_list):
    if self.env.context.get("mail_create_bypass_create_check") is self._bypass_create_check:
        self = self.sudo()
    for vals in vals_list:
        if "channel_id" not in vals:
            raise UserError(
                _(
                    "It appears you're trying to create a channel member, but it seems like you forgot to specify the related channel. "
                    "To move forward, please make sure to provide the necessary channel information."
                )
            )
        channel = self.env["discuss.channel"].browse(vals["channel_id"])
    return super(ChannelMember, self).create(vals_list)

ChannelMember.create = create


class IrAsset(models.Model):
    _inherit = 'ir.asset'

    def _fill_asset_paths(self, bundle, asset_paths, seen, addons, installed, **assets_params):
        super()._fill_asset_paths( bundle, asset_paths, seen, addons, installed, **assets_params)
        is_whatsapp_installed = self.env['ir.module.module'].sudo().search(
            [('state', '=', 'installed'), ('name', 'in', ['whatsapp_extended', 'tus_meta_wa_discuss'])])
        if is_whatsapp_installed and bundle == 'web.assets_backend':
            path = self._get_paths('odoo_facebook_instagram_messenger/static/src/xml/AgentsList.xml', installed)
            asset_paths.remove(path, bundle)