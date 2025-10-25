import hashlib
import hmac
import json
import logging
import pprint

from odoo import http
from odoo.http import request

_logger = logging.getLogger(__name__)


class PosPaymobController(http.Controller):

    @http.route(
        "/pos_paymob/notification",
        type="json",
        auth="public",
        csrf=False,
        methods=["POST"],
    )
    def paymob_return(self, **kwargs):
        raw_data = request.httprequest.get_data()

        try:
            json_data = json.loads(raw_data)
        except json.JSONDecodeError:
            _logger.error("Invalid JSON data received.")
            return {"error": "Invalid JSON data"}, 400

        _logger.info("Paymob Parsed JSON data: %s", pprint.pformat(json_data))
        event_type = json_data.get("type")

        if event_type == "TRANSACTION":
            return self._handle_transaction(json_data)

        else:
            _logger.error("Invalid data received %s", json_data)
            return {"error": "Invalid event type"}, 400

    def _handle_transaction(self, json_data):
        try:
            # Verify HMAC
            received_hmac = request.httprequest.args.get("hmac")
            terminal_id = json_data["obj"]["terminal_id"]
            # Extract transaction details
            transaction_obj = json_data["obj"]
            is_refunded = transaction_obj.get("is_refunded", False)
            is_voided = transaction_obj.get("is_voided", False)
            is_void = transaction_obj.get("is_void", False)
            success = transaction_obj.get("success", False)
            error_occurred = transaction_obj.get("error_occured", False)

            record = (
                request.env["pos.payment.method"]
                .sudo()
                .search([("paymob_terminal_id", "=", terminal_id)], limit=1)
            )
            hmac_secret = record.paymob_hmac if record else None
            calculated_hmac = self._calculate_hmac(hmac_secret, json_data)

            if received_hmac != calculated_hmac and not is_refunded:
                _logger.error("HMAC verification failed")
                return {"error": "HMAC mismatch"}, 400

            # extract information and validate
            terminal_id = json_data["obj"]["terminal_id"]
            transaction_info = json_data["obj"]["order"]["merchant_order_id"]
            time_stamp, pos_session_id, order_uuid = transaction_info.split("--")

            paymob_pm_sudo = (
                request.env["pos.payment.method"]
                .sudo()
                .search([("paymob_terminal_id", "=", terminal_id)], limit=1)
            )
            if not paymob_pm_sudo:
                _logger.error("Terminal ID not found in odoo system")
                return {"error": "Terminal ID not found"}, 400
            pos_session_sudo = (
                request.env["pos.session"].sudo().browse(int(pos_session_id))
            )
            if not pos_session_sudo:
                _logger.error("POS session not found in odoo system")
                return {"error": "POS session not found"}, 400

            

            # Log transaction type
            if is_refunded:
                refunded_amount = transaction_obj.get("refunded_amount_cents", 0)
                _logger.info(
                    "Paymob: Refund callback - Amount: %s cents, Success: %s",
                    refunded_amount,
                    success,
                )
                # Handle refund transaction
                if success:
                    self._handle_refund_order(transaction_obj, pos_session_id, order_uuid)
            elif is_voided or is_void:
                _logger.info("Paymob: Void callback - Success: %s", success)
                # Handle void transaction
                if success:
                    self._handle_void_order(transaction_obj, pos_session_id, order_uuid)
            elif error_occurred:
                _logger.info("Paymob: Error callback - Transaction failed")
            else:
                _logger.info("Paymob: Payment callback - Success: %s", success)

            # Store the response
            paymob_pm_sudo.paymob_latest_response = json.dumps(json_data)

            return "OK", 200

        except Exception as e:
            _logger.error("Error handling transaction: %s", e)
            return {"error": "Error handling transaction"}, 400

    def _handle_refund_order(self, transaction_obj, pos_session_id, order_uuid):
        """Handle refund transaction and update the existing order"""
        # Add this line for debugging
        self._debug_order_search(pos_session_id, order_uuid)
        
        try:
            refunded_amount_cents = transaction_obj.get("refunded_amount_cents", 0)
            refunded_amount = refunded_amount_cents / 100.0  # Convert to currency units
            transaction_id = transaction_obj.get("id")
            original_amount_cents = transaction_obj.get("amount_cents", 0)
            original_amount = original_amount_cents / 100.0
            
            _logger.info("Paymob: Processing refund - Amount: %s, Original: %s, Transaction: %s", 
                       refunded_amount, original_amount, transaction_id)
            
            # Method 1: Search by session and UUID in pos_reference
            pos_order = request.env['pos.order'].sudo().search([
                ('session_id', '=', int(pos_session_id)),
                ('pos_reference', 'ilike', f'%{order_uuid}%')
            ], limit=1)
            
            if not pos_order:
                # Method 2: Search by session and UUID in name
                pos_order = request.env['pos.order'].sudo().search([
                    ('session_id', '=', int(pos_session_id)),
                    ('name', 'ilike', f'%{order_uuid}%')
                ], limit=1)
            
            if not pos_order:
                # Method 3: Search by session and payment amount (most reliable)
                _logger.info("Paymob: UUID not found in order fields, searching by amount")
                pos_orders = request.env['pos.order'].sudo().search([
                    ('session_id', '=', int(pos_session_id)),
                    ('state', 'in', ['paid', 'done', 'invoiced'])
                ])
                
                # Find order with matching Paymob payment amount
                for order in pos_orders:
                    for payment in order.payment_ids:
                        if (payment.payment_method_id.use_payment_terminal == 'paymob' and 
                            payment.payment_status == 'done' and
                            abs(payment.amount - original_amount) < 0.01):
                            pos_order = order
                            _logger.info("Paymob: Found order %s by payment amount %s", order.name, payment.amount)
                            break
                    if pos_order:
                        break

            if pos_order:
                _logger.info("Paymob: Found original order %s for refund", pos_order.name)
                
                # Find the payment line that corresponds to this transaction
                payment_line = None
                for line in pos_order.payment_ids:
                    if (line.payment_method_id.use_payment_terminal == 'paymob' and 
                        line.payment_status == 'done' and
                        abs(line.amount - original_amount) < 0.01):
                        payment_line = line
                        _logger.info("Paymob: Found matching payment line - Amount: %s", line.amount)
                        break
                
                if payment_line:
                    _logger.info("Paymob: Creating refund payment line")
                    
                    # Create a refund payment line
                    refund_payment_vals = {
                        'pos_order_id': pos_order.id,
                        'amount': -refunded_amount,  # Negative amount for refund
                        'payment_method_id': payment_line.payment_method_id.id,
                        'payment_status': 'done',
                        'transaction_id': f"REFUND_{transaction_id}",
                    }
                    
                    # Only add card fields if they exist on the original payment
                    if hasattr(payment_line, 'card_type') and payment_line.card_type:
                        refund_payment_vals['card_type'] = payment_line.card_type
                    if hasattr(payment_line, 'cardholder_name') and payment_line.cardholder_name:
                        refund_payment_vals['cardholder_name'] = payment_line.cardholder_name
                    
                    try:
                        # Create the refund payment line
                        refund_payment = request.env['pos.payment'].sudo().create(refund_payment_vals)
                        _logger.info("Paymob: Created refund payment line with ID: %s", refund_payment.id)
                        
                        # Update order amounts
                        old_amount_paid = pos_order.amount_paid
                        old_amount_return = pos_order.amount_return
                        
                        pos_order.amount_paid -= refunded_amount
                        pos_order.amount_return += refunded_amount
                        
                        _logger.info("Paymob: Updated order amounts - Paid: %s->%s, Return: %s->%s", 
                                   old_amount_paid, pos_order.amount_paid, 
                                   old_amount_return, pos_order.amount_return)
                        
                        # Determine appropriate order state based on remaining payments
                        total_valid_payments = sum(
                            p.amount for p in pos_order.payment_ids.filtered(
                                lambda p: p.payment_status == 'done' and p.amount > 0
                            )
                        )
                        
                        pos_order.state = 'cancel'
                        
                        _logger.info("Paymob: Successfully processed refund for order %s - Final state: %s", 
                                   pos_order.name, pos_order.state)
                        
                    except Exception as create_error:
                        _logger.error("Paymob: Error creating refund payment: %s", create_error)
                        import traceback
                        _logger.error("Paymob: Traceback: %s", traceback.format_exc())
                        
                else:
                    _logger.warning("Paymob: Could not find matching payment line for refund in order %s", 
                                  pos_order.name)
                    # Debug: Log all payment lines
                    for line in pos_order.payment_ids:
                        _logger.info("  - Payment ID %s: Amount %s, Method: %s, Status: %s, Terminal: %s", 
                                   line.id, line.amount, line.payment_method_id.name, 
                                   line.payment_status, getattr(line.payment_method_id, 'use_payment_terminal', 'none'))
            else:
                _logger.warning("Paymob: Could not find original order for refund. Session: %s, UUID: %s", 
                              pos_session_id, order_uuid)
                
        except Exception as e:
            _logger.error("Paymob: Error handling refund order: %s", e)
            import traceback
            _logger.error("Paymob: Traceback: %s", traceback.format_exc())

    def _handle_void_order(self, transaction_obj, pos_session_id, order_uuid):
        """Handle void transaction and update the existing order"""
        try:
            transaction_id = transaction_obj.get("id")
            
            # Find the original order
            pos_order = request.env['pos.order'].sudo().search([
                ('session_id', '=', int(pos_session_id)),
                ('pos_reference', 'ilike', f'%{order_uuid}%')
            ], limit=1)
            
            if not pos_order:
                pos_order = request.env['pos.order'].sudo().search([
                    ('session_id', '=', int(pos_session_id)),
                    ('name', 'ilike', f'%{order_uuid}%')
                ], limit=1)
            
            if pos_order:
                _logger.info("Paymob: Found original order %s for void", pos_order.name)
                
                # Find and update the payment line
                for payment_line in pos_order.payment_ids:
                    if (payment_line.payment_method_id.use_payment_terminal == 'paymob' and 
                        payment_line.payment_status == 'done'):
                        
                        # Mark the payment as voided
                        payment_line.payment_status = 'reversed'
                        payment_line.transaction_id = f"VOID_{transaction_id}"
                        
                        # Update order amounts
                        pos_order.amount_paid -= payment_line.amount
                        
                        # Add a note to the order
                        order_note = pos_order.note or ""
                        void_note = f"\nVOID: Payment voided via Paymob (Transaction: {transaction_id})"
                        pos_order.note = order_note + void_note
                        
                        # Mark order as cancelled if no valid payments remain
                        valid_payments = pos_order.payment_ids.filtered(lambda p: p.payment_status == 'done')
                        if not valid_payments or sum(valid_payments.mapped('amount')) == 0:
                            pos_order.state = 'cancel'
                            _logger.info("Paymob: Order %s marked as cancelled due to void", pos_order.name)
                        
                        break
                
                _logger.info("Paymob: Processed void for order %s", pos_order.name)
            else:
                _logger.warning("Paymob: Could not find original order for void. Session: %s, UUID: %s", 
                              pos_session_id, order_uuid)
                
        except Exception as e:
            _logger.error("Paymob: Error handling void order: %s", e)

    def _calculate_hmac(self, key, json_data):
        try:
            data = json_data["obj"].copy()
            data["order"] = data["order"]["id"]

            data["is_3d_secure"] = "true" if data["is_3d_secure"] else "false"
            data["is_auth"] = "true" if data["is_auth"] else "false"
            data["is_capture"] = "true" if data["is_capture"] else "false"
            data["is_refunded"] = "true" if data["is_refunded"] else "false"
            data["is_standalone_payment"] = (
                "true" if data["is_standalone_payment"] else "false"
            )
            data["is_voided"] = "true" if data["is_voided"] else "false"
            data["success"] = "true" if data["success"] else "false"
            data["error_occured"] = "true" if data["error_occured"] else "false"
            data["has_parent_transaction"] = (
                "true" if data["has_parent_transaction"] else "false"
            )
            data["pending"] = "true" if data["pending"] else "false"
            data["source_data_pan"] = data["source_data"]["pan"]
            data["source_data_type"] = data["source_data"]["type"]
            data["source_data_sub_type"] = data["source_data"]["sub_type"]

            concatenated_string = (
                str(data["amount_cents"])
                + str(data["created_at"])
                + str(data["currency"])
                + str(data["error_occured"])
                + str(data["has_parent_transaction"])
                + str(data["id"])
                + str(data["integration_id"])
                + str(data["is_3d_secure"])
                + str(data["is_auth"])
                + str(data["is_capture"])
                + str(data["is_refunded"])
                + str(data["is_standalone_payment"])
                + str(data["is_voided"])
                + str(data["order"])
                + str(data["owner"])
                + str(data["pending"])
                + str(data["source_data_pan"])
                + str(data["source_data_sub_type"])
                + str(data["source_data_type"])
                + str(data["success"])
            )
            calculated_hmac = hmac.new(
                key.encode("utf-8"), concatenated_string.encode("utf-8"), hashlib.sha512
            ).hexdigest()

            return calculated_hmac
        except Exception as e:
            _logger.error("Error calculating HMAC: %s", e)
            return None

    def _debug_order_search(self, pos_session_id, order_uuid):
        """Debug method to understand how orders are stored"""
        try:
            # Get all orders in the session
            all_orders = request.env['pos.order'].sudo().search([
            ('session_id', '=', int(pos_session_id))
            ])
            
            _logger.info("=== DEBUG: Order Search ===")
            _logger.info("Looking for UUID: %s in session: %s", order_uuid, pos_session_id)
            _logger.info("Found %d orders in session:", len(all_orders))
            
            for order in all_orders:
                _logger.info("Order ID: %s", order.id)
                _logger.info("  - pos_reference: '%s'", order.pos_reference)
                _logger.info("  - name: '%s'", order.name)
                _logger.info("  - amount_total: %s", order.amount_total)
                _logger.info("  - state: %s", order.state)
                
                # Check if this order matches the UUID
                if order_uuid in order.pos_reference or order_uuid in order.name:
                    _logger.info("  - FOUND MATCHING ORDER!")


                # Check payment lines
                for payment in order.payment_ids:
                    if payment.payment_method_id.use_payment_terminal == 'paymob':
                        _logger.info("  - Paymob payment: Amount %s, Status: %s", 
                            payment.amount, payment.payment_status)
                    _logger.info("  ---")
                
                _logger.info("=== END DEBUG ===")
            
        except Exception as e:
            _logger.error("Debug error: %s", e)
