
from odoo import models, fields, api
from odoo.tools import split_every, SQL
from odoo.http import request
from psycopg2 import errors
from datetime import timedelta
import logging
_logger = logging.getLogger(__name__)

class WebsiteVisitor(models.Model):
    _inherit = 'website.visitor'

    def _upsert_visitor(self, access_token, force_track_values=None):

        return (1, 'skipped')
    
        """ Based on the given `access_token`, either create or return the
        related visitor if exists, through a single raw SQL UPSERT Query.

        It will also create a tracking record if requested, in the same query.

        :param access_token: token to be used to upsert the visitor
        :param force_track_values: an optional dict to create a track at the
            same time.
        :return: a tuple containing the visitor id and the upsert result (either
            `inserted` or `updated).
        """
        create_values = {
            'access_token': access_token,
            'lang_id': request.lang.id,
            # Note that it's possible for the GEOIP database to return a country
            # code which is unknown in Odoo
            'country_code': request.geoip.get('country_code'),
            'website_id': request.website.id,
            'timezone': self._get_visitor_timezone() or None,
            'write_uid': self.env.uid,
            'create_uid': self.env.uid,
            # If the access_token is not a 32 length hexa string, it means that the
            # visitor is linked to a logged in user, in which case its partner_id is
            # used instead as the token.
            'partner_id': None if len(str(access_token)) == 32 else access_token,
        }

        visitor = self.sudo().search([('access_token', '=', access_token)], limit=1)
        if visitor:
            # update fields safely
            write_data = {
                'last_connection_datetime': fields.Datetime.now(),
                'visit_count': visitor.visit_count + 1 if visitor.last_connection_datetime < fields.Datetime.now() - timedelta(hours=8) else visitor.visit_count,
                'lang_id': request.lang.id,
                'timezone': self._get_visitor_timezone() or None,
            }
            _logger.info("--- write_data ---%s",write_data)
            visitor.write(write_data)
            if force_track_values:
                create_data = {
                    'visitor_id': visitor.id,
                    'url': force_track_values['url'],
                    'page_id': force_track_values.get('page_id'),
                    'visit_datetime': fields.Datetime.now(),
                }
                _logger.info("--- create_data ---%s",create_data)
                # visitor = self.env['website.track'].sudo().create(create_data)
                self.env['website.track'].sudo().create(create_data)
            return (visitor.id, 'updated')


        query = SQL("""
            INSERT INTO website_visitor (
                partner_id, access_token, last_connection_datetime, visit_count, lang_id,
                website_id, timezone, write_uid, create_uid, write_date, create_date, country_id)
            VALUES (
                %(partner_id)s, %(access_token)s, now() at time zone 'UTC', 1, %(lang_id)s,
                %(website_id)s, %(timezone)s, %(create_uid)s, %(write_uid)s,
                now() at time zone 'UTC', now() at time zone 'UTC', (
                    SELECT id FROM res_country WHERE code = %(country_code)s
                )
            )
            ON CONFLICT (access_token)
            DO UPDATE SET
                last_connection_datetime=excluded.last_connection_datetime,
                visit_count = CASE WHEN website_visitor.last_connection_datetime < NOW() AT TIME ZONE 'UTC' - INTERVAL '8 hours'
                                    THEN website_visitor.visit_count + 1
                                    ELSE website_visitor.visit_count
                                END
            RETURNING id, CASE WHEN create_date = now() at time zone 'UTC' THEN 'inserted' ELSE 'updated' END AS upsert
        """, **create_values)

        if force_track_values:
            query = SQL("""
                WITH visitor AS (
                    %(query)s, %(url)s AS url, %(page_id)s AS page_id
                ), track AS (
                    INSERT INTO website_track (visitor_id, url, page_id, visit_datetime)
                    SELECT id, url, page_id::integer, now() at time zone 'UTC' FROM visitor
                )
                SELECT id, upsert from visitor;
                """,
                query=query,
                url=force_track_values['url'],
                page_id=force_track_values.get('page_id'),
            )
          
        # [result] = self.env.execute_query(query)
        # return result
    
        try:
            _logger.info("Query Executed ...  %s", query)
            [result] = self.env.execute_query(query)
            return result

        # except errors.SerializationFailure:
        except Exception as e:

            # Handle gracefully instead of raising error
            _logger.info("Concurrent update detected in website.visitor UPSERT, ignoring... %s",e)
            self.env.cr.rollback()  # reset transaction

            # Option 1: Return a safe fallback
            visitor = self.sudo().search([('access_token', '=', access_token)], limit=1)
            if visitor:
                return (visitor.id, 'updated')
            else:
                return (1, 'skipped')







