import errno
from odoo import http
from odoo.http import request
import logging
from datetime import date, timedelta
import calendar


_logger = logging.getLogger(__name__)

class AltSupportBridgeServerCreateTask(http.Controller):

    @http.route('/alt_support_bridge_server/ensure_project', type='json', auth='user')
    def ensure_project(self, channel_id, channel_name, author_id, message):

        _logger.info("--------------? message %s",message)
        
        channel = request.env['discuss.channel'].browse(int(channel_id))
        if not channel.exists():
            return {'message': "Something Wrong !!!!!"}

        if not author_id:
            return {'message': "Something Wrong !!!!!"}
        
        today = date.today()
        first_day = today.replace(day=1)
        last_day = today.replace(day=calendar.monthrange(today.year, today.month)[1])
        
        subscriptions = request.env['subscription.package'].search([
            ('start_date','>=',first_day),
            ('next_invoice_date', '<=', last_day),
            ('stage_id.category','=','progress'),
            ('discuss_channel_id','=',channel.id)
        ],limit=1)

        # subscriptions = request.env['subscription.package'].search([
        #     ('partner_id','=',author_id),
        #     ('start_date','>=',first_day),
        #     ('next_invoice_date', '<=', last_day),
        #     ('stage_id.category','=','progress')
        # ],limit=1)

        if not subscriptions:
            return {'error': "No active subscription found. Please check your subscription."}

        if not subscriptions.product_line_ids:
            return {'error': f"Subscription '{subscriptions.name}' has no timeline set. Please check."}

        # Compare allocated vs. consumed hours
        allocated_hours = sum(subscriptions.product_line_ids.mapped('product_qty'))
        consumed_hours = sum(subscriptions.task_ids.mapped('allocated_hours'))

        if consumed_hours >= allocated_hours:
            return {'error': f"Subscription '{subscriptions.name}' has exhausted its allocated time."}

        
        project = channel.project_id
        if not project:
            _logger.warning("Linked project missing or deleted for channel %s. Creating new project.", channel.id)
            project = request.env['project.project'].sudo().create({
                'name': channel_name
            })
            channel.project_id = project

        return {'project_id': project.id , 'user_id' : request.env.user.id , 'subscriptions' : subscriptions.id, 'message' : message}
    
    