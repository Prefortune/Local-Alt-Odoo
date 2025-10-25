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


class CargoPickUpPoint(models.Model):
    _name = 'cargo.pick.up.point'
    _description = 'Cargo Pick Up Point'
    _rec_name = 'distribution_point_pame'

    distribution_point_id = fields.Char(string='DistributionPointID')
    distribution_point_pame = fields.Char(string='DistributionPointName')
    cityname = fields.Char(string='CityName')
    streetname = fields.Char(string='StreetName')
    streetnum  = fields.Char(string='StreetNum')


    def get_cargo_pick_up_point(self):

        url = "https://api.cargo.co.il/Webservice/getPickUpPoints"
        header = {
            "Content-Type": "application/json",
        }
        payload = {
                "userName": "Cargo",
                "password": "Crg2468",
                "APICode": 924568
        }

        response = requests.post(url, headers=header, json=payload)
        result = response.json()
        print(result)

        points = result.get("PointsDetails")
        print(points)
        for po in points:
           
            existing_record = self.search([('distribution_point_id', '=', po.get("DistributionPointID"))], limit=1)
            if not existing_record:
                self.create({
                    'distribution_point_id': po.get("DistributionPointID"),
                    'distribution_point_pame': po.get("DistributionPointName"),
                    'cityname': po.get("CityName"),
                    'streetname': po.get("StreetName"),
                    'streetnum': po.get("StreetNum"),

                })
            else:
                existing_record.write({
                    'distribution_point_pame': po.get("DistributionPointName"),
                    'cityname': po.get("CityName"),
                    'streetname': po.get("StreetName"),
                    'streetnum': po.get("StreetNum"),
                })

class StockPicking(models.Model):
    _inherit = 'stock.picking'

    carrier_id = fields.Many2one("delivery.carrier", string="Carrier", check_company=True)
    cargo_pick_up_point_id = fields.Many2one('cargo.pick.up.point', string='Cargo Pick Up Point')
    show_or_not = fields.Boolean(string='Show or Not', default=False, compute='_compute_show_or_not')
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
    
    @api.depends('carrier_id')
    def _compute_show_or_not(self):
        for rec in self:
            if rec.carrier_id and not rec.sale_id.woo_instance_id:
                if rec.carrier_id.cargo_delivery_type == 'BOX' or rec.carrier_id.cargo_delivery_type == 'box':
                    rec.show_or_not = True
                else:
                    rec.show_or_not = False
            else:
                rec.show_or_not = False

    
    def action_create_shipment_stock_picking(self):
        url = "https://api.cargo.co.il/Webservice/CreateShipment"
        headers = {
            "Content-Type": "application/json"
        }
        content_description = ''
        for line in self.sale_id.order_line:
            content_description += line.name

        note = ""

        # if self.sale_order_note:
        #     note = self.sale_order_note

        if self.sale_id:
            # note = self.sale_id.note old code direct take a note from sales order note field
            if self.sale_id.note:
                note = self.sale_id.cargo_ship_note  # custom field is added for take a note from sales order
        
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
                "PaymentMethod": self.sale_id.payment_gateway_id.name,
                "Note": note,
                "customerCode": self.carrier_id.customer_code
            }
        }
        if self.carrier_id.cargo_delivery_type == 'BOX' or self.carrier_id.cargo_delivery_type == 'box':

            # distribution_point_id = ''
            if self.cargo_pick_up_point_id.distribution_point_id:
                distribution_point_id = self.cargo_pick_up_point_id.distribution_point_id 

            if self.sale_id and self.sale_id.woo_instance_id:
                order = self.sale_id
                instance_id = self.env['woo.instance.ept'].search([('id','=',order.woo_instance_id.id)])
                if instance_id:
                    print("in box")
                    print("in box")
                    print("new box")
                    # get boxpoint id from woo order
                    # boxPointId = ''
                    print("order  ",order)
                    print("order  ",order.woo_instance_id)
                    print("order  ",order.woo_instance_id.id)
                    instance_id = self.env['woo.instance.ept'].search([('id','=',order.woo_instance_id.id)])
                    print("instance id  ",instance_id)
                    location = instance_id.woo_host
                    cons_key = instance_id.woo_consumer_key
                    sec_key = instance_id.woo_consumer_secret
                    version = 'wc/v3'
                    print("before wcapi")
                    print("url ", location)
                    wcapi = API(url=location,
                                consumer_key=cons_key,
                                consumer_secret=sec_key,
                                version=version
                                )
                    print("after ---------- ",wcapi)
                    parsed_data = wcapi.get("orders/"+str(order.woo_order_number)).json()
                    if parsed_data:
                        ele = parsed_data
                        if 'meta_data' in ele:
                            for meta in ele['meta_data']:
                                if meta['key'] == 'cargo_DistributionPointID':
                                    boxPointId = meta['value']
                else:
                    if not distribution_point_id:
                        raise UserError(_('Please select a distribution point for the cargo pickup point.'))
                    else:
                        boxPointId = distribution_point_id

            else:
                if not distribution_point_id:
                    raise UserError(_('Please select a distribution point for the cargo pickup point.'))
                else:
                    boxPointId = distribution_point_id

                # boxPointId = distribution_point_id

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
