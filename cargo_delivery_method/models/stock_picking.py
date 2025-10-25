import urllib
import requests
import json
from odoo.exceptions import UserError
from datetime import date
from woocommerce import API
from markupsafe import Markup
from odoo.tools import html_keep_url
from odoo import api, fields, _, models
from datetime import datetime
from odoo.tools import config


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    waybill_link = fields.Char(string='WayBill Link')
    cargo_response = fields.Text("Cargo Response")
    shipment_status = fields.Selection(
        [
            ('1', 'Open'),
            ('2', 'Transferred to courier'),
            ('3', 'Done'),
            ('4', 'Collected by CARGO'),
            ('5', 'Return from a double'),
            ('7', 'Execution approved'),
            ('8', 'Cancelled'),
            ('9', 'Second delivery'),
            ('12', 'Pending shipping'),
            ('51', 'On the way to Delivery point'),
            ('55', 'Delivery point'),
            ('52', 'In Delivery point'),
        ],
        'Shipment Status', copy=False, )


    def action_create_shipment_stock_picking(self):
        url = "https://api.cargo.co.il/Webservice/CreateShipment"
        headers = {
            "Content-Type": "application/json"
        }
        content_description = ''
        for line in self.sale_id.order_line:
            content_description += line.name
        note = ""
        if self.sale_order_note:
            note = self.sale_order_note
        carrierName = "CARGO EXRESSS"
        payload = {
            "Method": "Ship",
            "Params": {
                "shipping_type": 1,
                "to_address": {
                    "name": self.partner_id.name,
                    # "company": self.company_id.name,
                    "street1": self.partner_id.street,
                    "city": self.partner_id.city,
                    "state": self.partner_id.state_id.name,
                    "zip": self.partner_id.zip,
                    "country": self.partner_id.country_id.name,
                    "phone": self.partner_id.phone,
                    "email": self.partner_id.email
                },
                "from_address": {
                    "name":"Leaf of Life",
                    "company":"Leaf of Life",
                    "street1":"4 רבי טרפון",
                    "city":"ירושלים",
                    "country": "IL",
                    "phone": "972587040400",
                    "email": "office@leafoflife.co.il"
                },
                "noOfParcel": 0,
                "doubleDelivery": 1,
                "TotalValue": self.sale_id.amount_total,
                "TransactionID": self.sale_id.name,
                "ContentDescription": content_description,
                "CashOnDeliveryType": 0,
                "CarrierName": carrierName,
                "CarrierService": self.carrier_id.cargo_delivery_type,
                "CarrierID": 1,
                "OrderID": self.sale_id.name,
                "PaymentMethod": self.sale_id.payment_method,
                "Note": note,
                "customerCode": self.carrier_id.customer_code
            }
        }
        if self.carrier_id.cargo_delivery_type == 'BOX' or self.carrier_id.cargo_delivery_type == 'box':
            print("in box")
            print("in box")
            # get boxpoint id from woo order
            boxPointId = ''
            so_obj = self.sale_id
            order = so_obj
            instance_id = self.env['woo.instance'].search([('id','=',order.woo_instance_id.id)])
            location = instance_id.url
            cons_key = instance_id.client_id
            sec_key = instance_id.client_secret
            version = 'wc/v3'

            wcapi = API(url=location,
                        consumer_key=cons_key,
                        consumer_secret=sec_key,
                        version=version
                        )
            parsed_data = wcapi.get("orders/"+str(order.woo_id)).json()
            if parsed_data:
                ele = parsed_data
                if 'meta_data' in ele:
                    for meta in ele['meta_data']:
                        if meta['key'] == 'cargo_DistributionPointID':
                            boxPointId = meta['value']
            payload['Params']['CarrierName'] = 'CARGO BOX'
            payload['Params']['CarrierService'] = 'cargo'
            payload['Params']['boxPointId'] = boxPointId
            payload['Params']['CarrierID'] = 0
        print(payload)
        payload_json = json.dumps(payload)
        print(payload_json)

        response = requests.post(url, headers=headers, data=payload_json)
        print(response)

        if response.status_code == 200:
            result = response.json()
            self.cargo_response = str(payload_json) + ' ' + str(result)
            print(json.dumps(result, indent=2))

            shipmentId = result.get("shipmentId")
            self.carrier_tracking_ref = shipmentId
        else:
            print("Request failed with status code:", {response.status_code})

    def action_shipment_status(self):
        print("action_check_shipment_status")
        url = "https://api.cargo.co.il/Webservice/CheckShipmentStatus"
        headers = {
            "Content-Type": "application/json"
        }

        payload = {
            "deliveryId": self.carrier_tracking_ref,
            "DeliveryType": self.carrier_id.cargo_delivery_type,
            "customerCode": self.carrier_id.customer_code
        }
        payload_json = json.dumps(payload)
        print(payload_json)

        response = requests.post(url, headers=headers, data=payload_json)
        print(response)

        if response.status_code == 200:
            result = response.json()
            self.shipment_status = str(result.get('deliveryStatus'))

            print(json.dumps(result, indent=2))
        else:
            print("Request failed with status code:", {response.status_code})

    def generate_shipment_label(self):
        print("generate_shipment_label")
        url = "https://api.cargo.co.il/Webservice/generateShipmentLabel"
        headers = {
            "Content-Type": "application/json"
        }

        payload = {
            "deliveryId": self.carrier_tracking_ref,
        }
        payload_json = json.dumps(payload)
        print(payload_json)

        response = requests.post(url, headers=headers, data=payload_json)
        print(response)

        if response.status_code == 200:
            result = response.json()
            print(json.dumps(result, indent=2))

            pdfLink = result.get("pdfLink")
            self.waybill_link = pdfLink

        else:
            print("Request failed with status code:", {response.status_code})
