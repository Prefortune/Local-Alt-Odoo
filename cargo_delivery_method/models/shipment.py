from odoo import models, fields, api
import requests
import json

class CargoDeliveryMethod(models.Model):
    _name = 'cargo.delivery'
    _description = 'Cargo Delivery'

    def action_create_shipment(self):
        url = "https://api.cargo.co.il/Webservice/CreateShipment"
        headers = {
            "Content-Type": "application/json"
        }

        payload = {
            "Method": "Ship",
            "Params": {
                "shipping_type": 1,
                "to_address": {
                    "name": "John Doe",
                    "company": "customer company",
                    "street1": "aluf david 171",
                    "city": "RAMAT GAN",
                    "state": "IL",
                    "zip": "90210",
                    "country": "IL",
                    "phone": "0522492797",
                    "email": "johndoe@gmail.com"
                },
                "from_address": {
                    "name": "John Doe",
                    "company": "my company",
                    "street1": "aluf david 171",
                    "city": "ramat gan",
                    "state": "il",
                    "zip": "90210",
                    "country": "il",
                    "phone": "039300039",
                    "email": "johndoe@gmail.com"
                },
                "noOfParcel": 0,
                "doubleDelivery": 1,
                "TotalValue": "123",
                "TransactionID": "ORDER2365",
                "ContentDescription": "Milk",
                "CashOnDeliveryType": 0,
                "CarrierName": "CARGO EXRESSS",
                "CarrierService": "CARGO",
                "CarrierID": 1,
                "OrderID": "",
                "PaymentMethod": "Paypal",
                "Note": "Ship by 25/06/2018",
                "customerCode": "2808"
            }
        }

        payload_json = json.dumps(payload)

        response = requests.post(url, headers=headers, data=payload_json)
        print(response)

        if response.status_code == 200:
            result = response.json()
            print(json.dumps(result, indent=2))
        else:
            print("Request failed with status code:", {response.status_code})
