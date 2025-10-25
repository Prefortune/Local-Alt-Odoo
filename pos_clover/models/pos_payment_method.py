import json
import logging
import requests
from odoo import _, fields, models
from odoo.exceptions import AccessDenied, ValidationError
import uuid


_logger = logging.getLogger(__name__)

CLOVER_BASE_URL = {
    "test": "https://sandbox.dev.clover.com/",
    "prod": "https://api.clover.com/",
}

class PosPaymentMethod(models.Model):
    _inherit = "pos.payment.method"

    def _get_payment_terminal_selection(self):
        return super(PosPaymentMethod, self)._get_payment_terminal_selection() + [
            ("clover", "Clover")
        ]

    clover_api_key = fields.Char("API Key", help="API Key for Clover", groups="base.group_erp_manager")
    clover_merchant_id = fields.Char("Merchant ID", help="Merchant ID for Clover", groups="base.group_erp_manager")
    clover_access_token = fields.Char("Access Token", help="OAuth Access Token for Clover", groups="base.group_erp_manager")
    clover_latest_response = fields.Char(copy=False, groups="base.group_erp_manager")
    clover_environment = fields.Selection(
        [
            ("test", "Sandbox"),
            ("prod", "Production"),
        ],
        string="Environment",
        default="test",
    )

    def _is_write_forbidden(self, fields):
        return super(PosPaymentMethod, self)._is_write_forbidden(
            fields - {"clover_latest_response"}
        )

    def get_latest_clover_status(self):
        """
        Get the latest Clover response for the POS Payment Method. Called from the POS front-end.
        """
        self.ensure_one()
        if not self.env.su and not self.env.user.has_group("point_of_sale.group_pos_user"):
            raise AccessDenied()

        latest_response = self.sudo().clover_latest_response
        _logger.info("Clover Latest Response:............................... %s", latest_response)
        latest_response = json.loads(latest_response) if latest_response else False
        _logger.info("Clover Latest Response Parsed: %s", latest_response)
        return latest_response
    

    def send_clover_request(self, data, operation):
        """
        Send a request to Clover API. Handles both sales and refunds.
        """
        self.ensure_one()
        try:
            if not self.clover_api_key or not self.clover_access_token:
                return {
                    "error": {
                        "status_code": 400,
                        "message": "Authentication Failed, Please set your API Key and Access Token first.",
                    }
                }

            headers = {
                "Authorization": f"Bearer {self.clover_access_token}",
                "Content-Type": "application/json",
            }

            amount_cents = int(data.get("amount_cents", 0))

            # === SALE FLOW ===
            if amount_cents > 0:
                # Create Order
                order_url = self._get_clover_endpoint("sale")
                sale_payload = self._prepare_sale_request(data)

                _logger.info("Clover URL (Create Order): %s", order_url)
                _logger.info("Clover Payload: %s", json.dumps(sale_payload, indent=2))
                resp = requests.post(order_url, json=sale_payload, headers=headers)
                _logger.info("Clover HTTP Status (Order): %s", resp.status_code)
                _logger.info("Clover Raw Response (Order): %s", resp.text)

                if resp.status_code not in (200, 201):
                    return {
                        "error": {
                            "status_code": resp.status_code,
                            "message": resp.json().get("message", "Failed to create Clover order."),
                        }
                    }

                order_data = resp.json()
                order_id = order_data.get("id")
                if not order_id:
                    return {
                        "error": {
                            "status_code": 400,
                            "message": "Clover order created but no order ID returned.",
                        }
                    }

                # Create Payment
                payment_url = f"{CLOVER_BASE_URL[self.clover_environment]}v3/merchants/{self.clover_merchant_id}/orders/{order_id}/payments"
                payment_payload = {
                    "amount": amount_cents,
                    "tipAmount": 0,
                    "externalPaymentId": sale_payload.get("external_id", f"PAY-{order_id}"),
                    "tender": {
                        "id": self._get_default_credit_tender_id()
                    },
                    "paymentType": "AUTH"
                }

                _logger.info("Clover URL (Payment): %s", payment_url)
                _logger.info("Clover Payment Payload: %s", json.dumps(payment_payload, indent=2))
                payment_resp = requests.post(payment_url, json=payment_payload, headers=headers)
                _logger.info("Clover HTTP Status (Payment): %s", payment_resp.status_code)
                _logger.info("Clover Raw Response (Payment): %s", payment_resp.text)

                if payment_resp.status_code not in (200, 201):
                    return {
                        "error": {
                            "status_code": payment_resp.status_code,
                            "message": payment_resp.json().get("message", "Failed to create Clover payment."),
                        }
                    }

                payment_data = payment_resp.json()
                latest_response = self.sudo().clover_latest_response
                _logger.info("..............................................: %s", latest_response)
                _logger.info("Clover Payment Response........................................................: %s",payment_data.get("cardTransaction", {}).get("authCode"),)
                normalized_status = {
                    "id": payment_data.get("id"),
                    "external_id": payment_payload["externalPaymentId"],
                    "status": payment_data.get("result"),
                }
                self.sudo().clover_latest_response = json.dumps(normalized_status)
                return normalized_status

            # # === REFUND FLOW ===
            # elif amount_cents < 0:
            #     refund_url = self._get_clover_endpoint("refund")
            #     refund_payload = {
            #         "amount": abs(amount_cents),
            #         "order": {"id": data.get("order_id")},
            #         "tender": {
            #             "id": self._get_default_credit_tender_id()
            #         }
            #     }

            #     _logger.info("Clover URL (Refund): %s", refund_url)
            #     _logger.info("Clover Refund Payload: %s", json.dumps(refund_payload, indent=2))
            #     refund_resp = requests.post(refund_url, json=refund_payload, headers=headers)
            #     _logger.info("Clover HTTP Status (Refund): %s", refund_resp.status_code)
            #     _logger.info("Clover Raw Response (Refund): %s", refund_resp.text)

            #     if refund_resp.status_code not in (200, 201):
            #         return {
            #             "error": {
            #                 "status_code": refund_resp.status_code,
            #                 "message": refund_resp.json().get("message", "Failed to create Clover refund."),
            #             }
            #         }

            #     refund_data = refund_resp.json()
            #     normalized_status = {
            #         "id": refund_data.get("id"),
            #         "status": "REFUNDED",
            #     }
            #     self.sudo().clover_latest_response = json.dumps(normalized_status)
            #     return normalized_status

            else:
                return {
                    "error": {
                        "status_code": 400,
                        "message": "Amount must be non-zero."
                    }
                }

        except Exception as e:
            _logger.error("Failed to process Clover request: %s", e)
            return {
                "error": {
                    "status_code": 400,
                    "message": "Failed to process Clover request. Please try again later.",
                }
            }


    def _get_default_credit_tender_id(self):
        """
        Fetch the first CREDIT_CARD tender ID for this merchant.
        """
        url = f"{CLOVER_BASE_URL[self.clover_environment]}v3/merchants/{self.clover_merchant_id}/tenders"
        headers = {"Authorization": f"Bearer {self.clover_access_token}"}
        resp = requests.get(url, headers=headers)
        if resp.status_code == 200:
            tenders = resp.json().get("elements", [])
            for t in tenders:
                # Match Clover's actual labelKey for credit card
                if t.get("labelKey") == "com.clover.tender.external_payment":
                    return t["id"]
        raise ValidationError(_("No Clover Credit Card tender found for this merchant."))
    def _get_clover_endpoint(self, operation):
        """
        Get the Clover endpoint based on the operation and environment.
        """
        if not self.clover_environment:
            raise ValidationError(_("Please select an environment for Clover."))
        endpoints = {
            "sale": f"v3/merchants/{self.clover_merchant_id}/orders",
            "refund": f"v3/merchants/{self.clover_merchant_id}/refunds",
            "auth": f"oauth/token",
        }
        return CLOVER_BASE_URL.get(self.clover_environment) + endpoints.get(operation)

    def _prepare_sale_request(self, data):
            """
            Prepare the request body for a Clover sale transaction.
            """
            request_body = {
                # "employee": { "id": data.get("employee_id")},
                "total": int(data.get("amount_cents", 0)),
                "currency": data.get("currency", "USD"),
                "external_id": self._generate_short_payment_id(),
                # "customers": [{ "id": data.get("customer_id")}],
                
            }
            # _logger.info("data................................: %s", data.get("customer_id"),".....................................employee  %s",data.get("employee_id"))
            # Add customer if provided

            return request_body
    
    def _generate_short_payment_id(self):
    # Generate a unique short ID (max 32 chars, Clover requirement)
     return uuid.uuid4().hex[:32]

    def check_clover_status(self):
        """
        Check if there's a new Clover response.
        """
        has_update = bool(self.clover_latest_response)
        if has_update:
            latest_response = self.clover_latest_response
            self.sudo().clover_latest_response = False
            return {
                "has_update": True,
                "latest_response": latest_response,
            }
        return {"has_update": False}