from odoo import fields , models, api
from odoo.exceptions import ValidationError,UserError
from calendar import monthrange

_secondsConverter = {
    'days': lambda interval: interval * 24 * 60 * 60,
    'hours': lambda interval: interval * 60 * 60,
    'weeks': lambda interval: interval * 7 * 24 * 60 * 60,
    'minutes': lambda interval: interval * 60,
}

class HelperUtils(models.AbstractModel):
    _name = "helper.utils"
    _description = "Helper Utilities"

    @api.model
    def get_graphql_query(self, type):
        query=''
        if type == 'webhook':
            query = """
                mutation webhookSubscriptionCreate($topic: WebhookSubscriptionTopic!, $webhookSubscription: WebhookSubscriptionInput!) {
                    webhookSubscriptionCreate(topic: $topic, webhookSubscription: $webhookSubscription) {
                        webhookSubscription {
                            id
                            callbackUrl
                            format
                        }
                        userErrors {
                            field
                            message
                        }
                    }
                }
            """
        
        return query


    @api.model
    def topic_mapping_field(self,topic):
        topic_field_mapping = {
            "PRODUCTS_CREATE": "product_create_webhook",
            "PRODUCTS_UPDATE": "product_update_webhook",
            "CUSTOMERS_CREATE": "customer_create_webhook",
            "CUSTOMERS_UPDATE": "customer_update_webhook",
            "DISCOUNTS_CREATE": "coupen_create_webhook",
            "DISCOUNTS_UPDATE": "coupen_update_webhook",
            "ORDERS_CREATE": "order_create_webhook",
            "ORDERS_UPDATED": "order_update_webhook",
        }

        return topic_field_mapping.get(topic)
    
    def get_cron_execution_time(self, cron_name):
        """
        This method is used to get the interval time of the cron.
        @param cron_name: External ID of the Cron.
        @return: Interval time in seconds.
        """
        process_queue_cron = self.env.ref(cron_name, False)
        if not process_queue_cron:
            raise UserError(
                _("Please upgrade the module. \n Maybe the job has been deleted, it will be recreated at "
                  "the time of module upgrade."))
        interval = process_queue_cron.interval_number
        interval_type = process_queue_cron.interval_type
        if interval_type == "months":
            days = 0
            current_year = fields.Date.today().year
            current_month = fields.Date.today().month
            for i in range(0, interval):
                month = current_month + i

                if month > 12:
                    if month == 13:
                        current_year += 1
                    month -= 12

                days_in_month = monthrange(current_year, month)[1]
                days += days_in_month

            interval_type = "days"
            interval = days
        interval_in_seconds = _secondsConverter[interval_type](interval)
        return interval_in_seconds

