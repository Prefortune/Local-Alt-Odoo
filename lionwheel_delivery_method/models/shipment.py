from odoo import models, fields, api
import requests
import json

class LionwheelDeliveryMethod(models.Model):
    _name = 'lionwheel.delivery'
    _description = 'Lionwheel Delivery'

    def action_create_shipment(self, carrier_id=None):
        # Get carrier configuration
        if carrier_id:
            carrier = self.env['delivery.carrier'].browse(carrier_id)
        else:
            # Get the first LionWheel carrier
            carrier = self.env['delivery.carrier'].search([('delivery_type', '=', 'fixed')], limit=1)
        
        if not carrier:
            print("No LionWheel carrier found. Please configure a delivery carrier.")
            return False
        
        # Get API configuration from carrier
        api_key = carrier.lionwheel_api_key
        company_id = carrier.lionwheel_company_id
        api_url = carrier.lionwheel_api_url or "https://members.lionwheel.com/api/v1/tasks/create"
        
        if not api_key:
            print("LionWheel API key not configured. Please set it in the delivery carrier settings.")
            return False
        
        if not company_id:
            print("Company ID not configured. Please set it in the delivery carrier settings.")
            return False
        
        # Build URL with API key
        url_with_key = f"{api_url}?key={api_key}"
        
        headers = {
            "Content-Type": "application/json"
        }

        payload = {
            "pickup_at": "13/05/2022",  # Date in dd/mm/yyyy format
            "company_id": company_id,  # From carrier configuration
            "notes": "Delivery notes",
            "original_order_id": "541b",  # Mandatory - unique ID in external system
            "source_city": "Ramat Gan",
            "source_street": "Aluf David",
            "source_number": "171",
            "source_zip_code": "90210",
            "source_floor": "",
            "source_apartment": "",
            "source_notes": "",
            "source_recipient_name": "John Doe",
            "source_phone": "039300039",
            "source_email": "johndoe@gmail.com",
            "source_latitude": "",
            "source_longitude": "",
            "destination_city": "Tel Aviv",  # Mandatory
            "destination_street": "Aluf David",  # Mandatory
            "destination_number": "171",  # Mandatory
            "destination_zip_code": "90210",
            "destination_floor": "",
            "destination_apartment": "",
            "destination_notes": "",
            "destination_recipient_name": "John Doe",
            "destination_phone": "0522492797",
            "destination_phone2": "",
            "destination_email": "johndoe@gmail.com",
            "destination_latitude": "",
            "destination_longitude": "",
            "delivery_method": "",
            "greeting": "",
            "gifter_name": "",
            "gifter_phone": "",
            "is_roundtrip": False,
            "packages_quantity": 1,
            "money_collect": 123,
            "is_self_pickup": False,
            "earliest": "",
            "latest": "",
            "line_items": [
                {
                    "name": "Milk",
                    "quantity": 1,
                    "price": "123.00"
                }
            ],
            "urgency": 0,
            "driver_id": ""
        }

        payload_json = json.dumps(payload)

        try:
            response = requests.post(url_with_key, headers=headers, data=payload_json)
            print(f"Response Status: {response.status_code}")
            print(f"Response Headers: {response.headers}")

            if response.status_code == 200:
                result = response.json()
                print("Success! Response:")
                print(json.dumps(result, indent=2))
                return result
            else:
                print(f"Request failed with status code: {response.status_code}")
                print(f"Response body: {response.text}")
                return False
                
        except requests.exceptions.RequestException as e:
            print(f"Request error: {e}")
            return False
