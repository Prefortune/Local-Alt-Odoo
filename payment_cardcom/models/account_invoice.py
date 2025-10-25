from odoo import models, fields ,api
import json
import requests
from odoo.exceptions import UserError , ValidationError
import logging
_logger = logging.getLogger(__name__)
from urllib.parse import parse_qs, urlparse

class AccountMove(models.Model):
    _inherit = 'account.move'

    transaction_id = fields.Char(string="Transaction ID #")
    invoice_transaction_id = fields.Char(string="Inv Transaction ID #")
    document_url = fields.Char(string="Document URL",copy=False)
    document_num = fields.Char(string="Document #",copy=False)
    refund_document_url = fields.Char(string="Refund Document URL",copy=False)
    refund_doc_num = fields.Char("Refund Doc #",copy=False)
    refund_doc_desc = fields.Char("Refund Doc Desc",copy=False)
    cardcom_doc_response_json = fields.Char("Refund Doc Response",copy=False)

    payment_provider_id = fields.Many2one(
        'payment.provider',
        string="Payment Provider",
        help="The payment provider used for this transaction."
    )
    is_refund_button = fields.Boolean(string="Refund Button Show Or Not", default=True)

    @api.model
    def create(self, vals):
        res = super(AccountMove, self).create(vals)
        _logger.info("Creating account move with vals: %s", res)
        sale_order_name = res.invoice_origin
        _logger.info("AccountMove sale_order_name %s",sale_order_name)
        if sale_order_name:
            sale_order = self.env['sale.order'].search([('name','=',sale_order_name)])
            _logger.info("AccountMove sale_order %s",sale_order)
            if sale_order and not res.transaction_id:
                transaction_number = sale_order.transaction_number
                _logger.info("AccountMove transaction_number %s",transaction_number)
                res.transaction_id = transaction_number
                res.is_refund_button = True
        return res
    
    def action_post(self):
        res = super(AccountMove, self).action_post()
        transaction_ids = self.transaction_ids and self.transaction_ids[0] or None
        _logger.info("Found %s transactions for SO %s", transaction_ids, self.name)
        sale_order = self.env['sale.order'].search([('name','=',self.invoice_origin)])
        if sale_order and transaction_ids:
            _logger.info("sale_order -------->>>> %s, %s, %s, %s, %s,",sale_order , sale_order.is_warning_div , transaction_ids , self.move_type , transaction_ids.provider_id.code)
            provider = transaction_ids.provider_id            
            if  sale_order.is_warning_div and transaction_ids and self.move_type == 'out_invoice' and transaction_ids.provider_id.code == 'cardcom' and not sale_order.is_j5_order_paid:
                username = provider.cardcom_api_name
                password = provider.cardcom_api_password  # or however it's stored
                terminal = provider.cardcom_terminal_number
                suspended_deal_id = self.transaction_id  # or wherever you store it

                if not all([username, password, terminal, suspended_deal_id]):
                    raise ValidationError("Missing required data for Suspended Deal activation")

                base_url = "https://secure.cardcom.solutions/Interface/SuspendedDealActivate.aspx"
                params = {
                "username": username,
                "userpassword": password,
                "terminalnumber": terminal,
                "SuspendedDealId": suspended_deal_id,
                }
                _logger.info("Activating suspended deal with params: %s", params)
                try:
                    response = requests.get(base_url, params=params)
                    _logger.info("HTTP status: %s", response.status_code)
                    response.raise_for_status()  # Raise error if not 2xx
                    result_text = response.text
                    _logger.info("Response content: %s", result_text)
                    # transaction_ids.cardcom_j5_response_json = result_text
                    transaction_ids.write({
                        'cardcom_j5_response_json' : result_text
                    })

                    response_dict = parse_qs(result_text or "")
                    _logger.info("J5 Response -> response_dict %s",response_dict)
                    invoice_number = None
                    if "InvoiceResponse.InvoiceNumber" in response_dict:
                        invoice_number = response_dict["InvoiceResponse.InvoiceNumber"][0]
                        document_num = response_dict["InvoiceResponse.InvoiceNumber"][0]
                    if invoice_number:
                        url = "https://secure.cardcom.solutions/api/v11/Documents/CreateDocumentUrl"
                        doc_payload = {
                            "ApiName": username,
                            "ApiPassword": password,
                            "DocumentType": "TaxInvoiceAndReceipt",  # or "Invoice" depending on your setup
                            "DocumentNumber": int(invoice_number),
                        }
                        headers = {"Content-Type": "application/json"}
                        response = requests.post(url, json=doc_payload, headers=headers)
                        # Example: store the document URL on the invoice
                        if response.status_code == 200:
                            data = response.json()
                            if data.get("ResponseCode") == 0:
                                self.document_url = data.get("DocUrl")
                                self.document_num = document_num

                    parsed_data = parse_qs(result_text)
                    _logger.info("parsed_data -> %s",parsed_data)
                    if provider.journal_id:
                            journal_id = provider.journal_id.id
                    else:
                        journal_id = self.env['account.journal'].search([('type', '=', 'bank')], limit=1).id

                    payment = self.env['account.payment'].create({
                        'partner_id': self.partner_id.id,
                        'ref': sale_order.name,
                        'amount': self.amount_total,
                        'journal_id': journal_id,
                    })

                    self.payment_id = payment.id
                    print("payment created")
                    payment.action_post()
                    # self.is_post_processed = True
                    print("action payment posted")
                    payment_move_line = payment.move_id.line_ids.filtered(
                                lambda line: line.account_id.reconcile and line.account_id.account_type == 'asset_receivable' and line.amount_residual != 0
                            )
                    invoice_move_line = self.line_ids.filtered(
                        lambda line: line.account_id.reconcile and line.account_id.account_type == 'asset_receivable' and line.amount_residual != 0
                    )
                    # Perform reconciliation
                    if payment_move_line and invoice_move_line:
                        (payment_move_line + invoice_move_line).reconcile()

                    internal_deal_number = parsed_data.get('InternalDealNumber', [None])[0]
                    # Optionally, parse the response if it's in XML/JSON format
                    # For simplicity, assuming success if status code is 200
                    self.message_post(body=f'CardCom J5 Transaction Approved Manully - {internal_deal_number}')
                    self.transaction_id = internal_deal_number
                    sale_order.is_warning_div = False
                    sale_order.message_post(body=f'CardCom J5 Transaction Approved Manully From Invoice - {internal_deal_number}')
                    _logger.info("Order %s marked as paid via suspended deal", self.name)
                except requests.RequestException as e:
                    _logger.exception("Error activating suspended deal")
                    raise ValidationError(f"Failed to activate suspended deal: {str(e)}")
            
            elif not sale_order.is_warning_div and transaction_ids and self.move_type == 'out_invoice' and transaction_ids.provider_id.code == 'cardcom' and sale_order.is_j5_order_paid:
                
                response_dict = parse_qs(transaction_ids.cardcom_j5_response_json or "")
                invoice_number = None
                if "InvoiceResponse.InvoiceNumber" in response_dict:
                    invoice_number = response_dict["InvoiceResponse.InvoiceNumber"][0]
                    document_num = response_dict["InvoiceResponse.InvoiceNumber"][0]
                if invoice_number:
                    provider = transaction_ids.provider_id
                    username = provider.cardcom_api_name
                    password = provider.cardcom_api_password  # or however it's stored
                    url = "https://secure.cardcom.solutions/api/v11/Documents/CreateDocumentUrl"
                    doc_payload = {
                        "ApiName": username,
                        "ApiPassword": password,
                        "DocumentType": "TaxInvoiceAndReceipt",  # or "Invoice" depending on your setup
                        "DocumentNumber": int(invoice_number),
                    }
                    headers = {"Content-Type": "application/json"}
                    response = requests.post(url, json=doc_payload, headers=headers)
                    # Example: store the document URL on the invoice
                    if response.status_code == 200:
                        data = response.json()
                        if data.get("ResponseCode") == 0:
                            self.document_url = data.get("DocUrl")
                            self.document_num = document_num

                if provider.journal_id:
                        journal_id = provider.journal_id.id
                else:
                    journal_id = self.env['account.journal'].search([('type', '=', 'bank')], limit=1).id

                payment = self.env['account.payment'].create({
                    'partner_id': self.partner_id.id,
                    'ref': sale_order.name,
                    'amount': self.amount_total,
                    'journal_id': journal_id,
                })

                self.payment_id = payment.id
                print("payment created")
                payment.action_post()
                # invoice.is_post_processed = True
                print("action payment posted")
                payment_move_line = payment.move_id.line_ids.filtered(
                            lambda line: line.account_id.reconcile and line.account_id.account_type == 'asset_receivable' and line.amount_residual != 0
                        )
                invoice_move_line = self.line_ids.filtered(
                    lambda line: line.account_id.reconcile and line.account_id.account_type == 'asset_receivable' and line.amount_residual != 0
                )
                # Perform reconciliation
                if payment_move_line and invoice_move_line:
                    (payment_move_line + invoice_move_line).reconcile()
        return res
    
    def action_refund_cardcom_payment(self):
        for res in self:
            if res.state != 'posted' and res.move_type != 'out_invoice':
                raise UserError("Only posted invoices can be refunded.")
            if not res.transaction_id:
                raise UserError("No transaction found for this invoice.")
            # if not res.transaction_ids:
            #     raise UserError("No transaction IDs found for this invoice.")

            # payment_provider = res.transaction_ids.provider_id
            transaction_uid = res.transaction_id
            provider = res.reversed_entry_id.transaction_ids.provider_id
            username = provider.cardcom_api_name
            password = provider.cardcom_api_password
            amount = res.amount_total
            url = "https://secure.cardcom.solutions/api/v11/Transactions/RefundByTransactionId"
            payload = {
                    "ApiName": username,          # replace with your Cardcom API name
                    "ApiPassword": password,  # replace with your Cardcom API password
                    "TransactionId": transaction_uid,             # <-- from your J5 response (InvoiceResponse.InvoiceNumber)
                    "PartialSum" : res.amount_total
            }
            headers = {
                "Content-Type": "application/json"
            }
            _logger.info("header: %s", headers)
            _logger.info("payload: %s", payload)
            response = requests.post(url, json=payload, headers=headers)
            print("Status Code:", response.status_code)
            result = response.json()
            _logger.info("action_refund_cardcom_payment Refund response: %s", result)
            res.is_refund_button = False
            if result.get("ResponseCode") == 0:
                res.message_post(body=f'CardCom Payment The amount of {amount} has been refunded successfully.')
                res.transaction_id = result.get('NewTranzactionId')
                # url = "https://secure.cardcom.solutions/api/v11/Documents/CreateDocumentUrl"
                # doc_payload = {
                #     "ApiName": username,
                #     "ApiPassword": password,
                #     "DocumentType": "TaxInvoiceAndReceiptRefund",  # or "Invoice" depending on your setup
                #     "DocumentNumber": int(res.refund_doc_num),
                # }
                # headers = {"Content-Type": "application/json"}
                # response = requests.post(url, json=doc_payload, headers=headers)
                # # Example: store the document URL on the invoice
                # data = response.json()
                # _logger.info("CreateDocumentUrl Refund Url ---->>> %s",data)
                # if data.get("ResponseCode") == 0:
                #     self.refund_document_url = data.get("DocUrl")
            else:
                raise UserError(f"Refund failed Something went wrong : {result}")


    def action_refund_cardcom(self):
        url = "https://secure.cardcom.solutions/api/v11/Documents/CancelDoc"
        document_number = ''
        if not self.transaction_id:
            raise UserError("No Document #")
        if not self.transaction_ids:
            raise UserError("No related transaction found")
        payment_provider_id = self.transaction_ids.provider_id

        payload = {
                "ApiName": payment_provider_id.cardcom_api_name,
                "ApiPassword": payment_provider_id.cardcom_api_password,
                "DocumentNumber": self.document_num,
                "DocumentType": "1",
                "IsCancelEmailSend": False,
                "IsSendSMS": False,
                "IsCreditCardCancelOnly": False
        }
        print('payload')
        print(payload)

        # Headers (optional)
        headers = {
            "Content-Type": "application/json",
        }

        # Send POST request
        response = requests.post(url, json=payload, headers=headers)
        data = response.json()
        # data = json.loads(data)
        print("data")
        print(data)
        new_doc_num = data.get('NewDocumentNumber',False)
        new_desc = data.get('Description',False)
        self.refund_doc_num = new_doc_num
        self.refund_doc_desc = new_desc
        refund_document_url = False
        if new_doc_num:
            refund_document_url = self.action_get_cardcom_document_url(payment_provider_id,'TaxInvoiceAndReceiptRefund',new_doc_num)
            self.refund_document_url = refund_document_url
            self.action_create_refund(new_doc_num,refund_document_url)

    def action_get_cardcom_document_url(self,payment_provider_id,document_type,document_number):
        print("action_get_cardcom_document_url")
        url = "https://secure.cardcom.solutions/api/v11/Documents/CreateDocumentUrl"
        payload = {
                "ApiName": payment_provider_id.cardcom_api_name,
                "ApiPassword": payment_provider_id.cardcom_api_password,
                "DocumentType": document_type,
                "DocumentNumber": document_number
        }
        print('payload')
        print(payload)
        # Headers (optional)
        headers = {
            "Content-Type": "application/json",
        }

        # Send POST request
        response = requests.post(url, json=payload, headers=headers)
        data = response.json()
        print('data')
        print(data)
        doc_url = data.get('DocUrl',False)
        self.refund_document_url = doc_url
        return doc_url

    def action_process(self):

        json_response = {
            "ResponseCode": 0,
            "Description": "העסקה בוצעה בהצלחה",
            "TerminalNumber": 1000,
            "LowProfileId": "73c183bf-0146-4cdd-8e02-08007fa37a07",
            "TranzactionId": 193884095,
            "ReturnValue": "Z12332Xaa",
            "Operation": "ChargeOnly",
            "UIValues": {
                "CardOwnerEmail": "testsite@test.co.il",
                "CardOwnerName": "Card Owner",
                "CardOwnerPhone": "039436100",
                "CardOwnerIdentityNumber": "040617649",
                "NumOfPayments": 1,
                "CardYear": 2025,
                "CardMonth": 11,
                "CustomFields": [],
                "IsAbroadCard": False
            },
            "DocumentInfo": {
                "ResponseCode": 0,
                "Description": "העסקה בוצעה בהצלחה",
                "DocumentType": "Receipt",
                "DocumentNumber": 571393,
                "AccountId": 0,
                "ForeignAccountNumber": None,
                "SiteUniqueId": None,
                "DocumentUrl": "https://secure.cardcom.solutions/api/v11/documents/DownloadDoc/?c=1&code=4XZ2Z7QGGeY+c8caYr4Q+0GpI+pkPytX/Gd7YaTtoXzkTVO/GjLEUQpXJKDYrbq3"
            },
            "TokenInfo": None,
            "SuspendedInfo": None,
            "TranzactionInfo": {
                "ResponseCode": 0,
                "Description": "העסקה בוצעה בהצלחה",
                "TranzactionId": 193884095,
                "TerminalNumber": 1000,
                "Amount": 123.67,
                "CoinId": 1,
                "CouponNumber": "38001032",
                "CreateDate": "2024-12-03T09:20:18",
                "Last4CardDigits": 0,
                "Last4CardDigitsString": "0000",
                "FirstCardDigits": 458000,
                "JParameter": "0",
                "CardMonth": 11,
                "CardYear": 25,
                "ApprovalNumber": "12345",
                "FirstPaymentAmount": 0.0,
                "ConstPaymentAmount": 0.0,
                "NumberOfPayments": 1,
                "CardInfo": "Israeli",
                "CardOwnerName": "Card Owner",
                "CardOwnerPhone": "039436100",
                "CardOwnerEmail": "testsite@test.co.il",
                "CardOwnerIdentityNumber": "040617649",
                "Token": "4cf8e168-261e-4613-8d20-000332986b24",
                "CardName": "ויזה רגיל",
                "SapakMutav": "",
                "Uid": "21121517002429612920744",
                "ConcentrationNumber": None,
                "DocumentNumber": 571393,
                "DocumentType": "Receipt",
                "Rrn": "",
                "Brand": "Visa",
                "Acquire": "Laumicard",
                "Issuer": "CAL",
                "PaymentType": "Standard",
                "CardNumberEntryMode": "Phone",
                "DealType": "Debit",
                "IsRefund": False,
                "DocumentUrl": None,
                "CustomFields": [],
                "IsAbroadCard": False
            },
            "ExternalPaymentVector": "NoneOrUnknown",
            "Country": "PK",
            "UTM": None
        }

        self.process_payment_response(json_response)

    def process_payment_response(self, json_response):
        transaction_id = json_response.get('TranzactionId')
        document_url = json_response.get('DocumentInfo', {}).get('DocumentUrl')

        self.transaction_id = transaction_id
        self.document_url = document_url

    def action_create_refund(self,document_num,document_url):
        refund = self._reverse_moves(default_values_list=[{
            'move_type': 'out_refund' if self.move_type == 'out_invoice' else 'in_refund',
        }])
        print("refund")
        print(refund)
        refund.document_url = document_url
        refund.document_num = document_num
        refund.action_post()
        print("action_post")


        payments = self.env['account.payment'].search([('ref', '=', self.invoice_origin)])
        print(payments)
        for payment in payments:
            new_payment = payment.copy()
            new_payment.payment_type = 'outbound'
            new_payment.action_post()

            payment_move_line = new_payment.move_id.line_ids.filtered(
                        lambda line: line.account_id.reconcile and line.account_id.account_type == 'asset_receivable' and line.amount_residual != 0
                    )
            invoice_move_line = refund.line_ids.filtered(
                lambda line: line.account_id.reconcile and line.account_id.account_type == 'asset_receivable' and line.amount_residual != 0
            )
            # Perform reconciliation
            if payment_move_line and invoice_move_line:
                (payment_move_line + invoice_move_line).reconcile()
