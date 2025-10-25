import requests
import json
from odoo.exceptions import UserError
from odoo import api, fields, _, models
from datetime import datetime


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    show_or_not = fields.Boolean(string='Show or Not', default=False, compute='_compute_show_or_not')
    waybill_link = fields.Char(string='WayBill Link')
    lionwheel_response = fields.Text("LionWheel Response")
    shipment_status = fields.Selection(
        [
            ('1', 'Open'),
            ('2', 'Transferred to courier'),
            ('3', 'Done'),
            ('4', 'Collected by LionWheel'),
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
                if rec.carrier_id.delivery_type == 'fixed' and rec.carrier_id.lionwheel_api_key:
                    rec.show_or_not = True
                else:
                    rec.show_or_not = False
            else:
                rec.show_or_not = False

    
    def action_create_shipment_stock_picking(self):
        # Get carrier configuration for LionWheel
        if not self.carrier_id:
            raise UserError(_('Please select a delivery carrier.'))
        
        api_key = self.carrier_id.lionwheel_api_key
        company_id = self.carrier_id.lionwheel_company_id
        api_url = self.carrier_id.lionwheel_api_url or "https://members.lionwheel.com/api/v1/tasks/create"
        
        if not api_key:
            raise UserError(_('LionWheel API key not configured. Please set it in the delivery carrier settings.'))
        
        if not company_id:
            raise UserError(_('Company ID not configured. Please set it in the delivery carrier settings.'))
        
        # Build URL with API key
        url_with_key = f"{api_url}?key={api_key}"
        
        headers = {
            "Content-Type": "application/json"
        }

        # Prepare content description from order lines
        content_description = ''
        line_items = []
        for line in self.sale_id.order_line:
            content_description += line.name + ', '
            line_items.append({
                "name": line.name,
                "quantity": int(line.product_uom_qty),
                "price": str(line.price_unit)
            })

        # Get notes
        note = ""
        if self.sale_id and self.sale_id.note:
            note = self.sale_id.cargo_ship_note  # custom field for cargo ship note

        # Get pickup date (default to today)
        pickup_date = datetime.now().strftime("%d/%m/%Y")

        # Build payload according to LionWheel API
        payload = {
            "pickup_at": pickup_date,
            "company_id": company_id,
            "notes": note,
            "original_order_id": self.sale_id.name,  # Mandatory - unique ID in external system
            # Source address (from carrier configuration)
            "source_city": self.carrier_id.lionwheel_source_city or "ירושלים",
            "source_street": self.carrier_id.lionwheel_source_street or "רבי טרפון",
            "source_number": self.carrier_id.lionwheel_source_number or "4",
            "source_zip_code": self.carrier_id.lionwheel_source_zip_code or "",
            "source_floor": "",
            "source_apartment": "",
            "source_notes": "",
            "source_recipient_name": self.carrier_id.lionwheel_source_recipient_name or "Leaf of Life",
            "source_phone": self.carrier_id.lionwheel_source_phone or "972587040400",
            "source_email": self.carrier_id.lionwheel_source_email or "office@leafoflife.co.il",
            "source_latitude": "",
            "source_longitude": "",
            # Destination address (customer)
            "destination_city": self.partner_id.city or "",  # Mandatory
            "destination_street": self.partner_id.street or "",  # Mandatory
            "destination_number": self.partner_id.street2 or "",  # Mandatory
            "destination_zip_code": self.partner_id.zip or "",
            "destination_floor": "",
            "destination_apartment": "",
            "destination_notes": "",
            "destination_recipient_name": self.partner_id.name or "",
            "destination_phone": self.partner_id.phone or "",
            "destination_phone2": self.partner_id.mobile or "",
            "destination_email": self.partner_id.email or "",
            "destination_latitude": "",
            "destination_longitude": "",
            "delivery_method": "",
            "greeting": "",
            "gifter_name": "",
            "gifter_phone": "",
            "is_roundtrip": self.carrier_id.lionwheel_is_roundtrip,
            "packages_quantity": self.carrier_id.lionwheel_default_packages_quantity,
            "money_collect": self.sale_id.amount_total if self.sale_id else 0,
            "is_self_pickup": self.carrier_id.lionwheel_is_self_pickup,
            "earliest": self.carrier_id.lionwheel_default_earliest or "",
            "latest": self.carrier_id.lionwheel_default_latest or "",
            "line_items": line_items,
            "urgency": int(self.carrier_id.lionwheel_default_urgency),
            "driver_id": ""
        }

        payload_json = json.dumps(payload)
        print(f"LionWheel API Request: {payload_json}")

        try:
            response = requests.post(url_with_key, headers=headers, data=payload_json)
            print(f"Response Status: {response.status_code}")

            if response.status_code == 200:
                result = response.json()
                self.lionwheel_response = str(payload_json) + ' ' + str(result)
                print("Success! Response:")
                print(json.dumps(result, indent=2))
                
                # Store the task ID as tracking reference
                task_id = result.get("id")
                if task_id:
                    self.carrier_tracking_ref = str(task_id)
                
                return result
            else:
                print(f"Request failed with status code: {response.status_code}")
                print(f"Response body: {response.text}")
                raise UserError(_(f"LionWheel API request failed: {response.status_code} - {response.text}"))
                
        except requests.exceptions.RequestException as e:
            print(f"Request error: {e}")
            raise UserError(_(f"LionWheel API request error: {str(e)}"))

    def action_shipment_status(self):
        print("action_check_shipment_status")
        
        if not self.carrier_id:
            raise UserError(_('Please select a delivery carrier.'))
        
        api_key = self.carrier_id.lionwheel_api_key
        api_url = self.carrier_id.lionwheel_api_url or "https://members.lionwheel.com/api/v1"
        
        if not api_key:
            raise UserError(_('LionWheel API key not configured. Please set it in the delivery carrier settings.'))
        
        if not self.carrier_tracking_ref:
            raise UserError(_('No tracking reference found. Please create a shipment first.'))
        
        # Build URL for getting task status
        url_with_key = f"{api_url}/tasks/{self.carrier_tracking_ref}?key={api_key}"
        
        headers = {
            "Content-Type": "application/json"
        }

        try:
            response = requests.get(url_with_key, headers=headers)
            print(f"Response Status: {response.status_code}")

            if response.status_code == 200:
                result = response.json()
                print("Success! Response:")
                print(json.dumps(result, indent=2))
                
                # Map LionWheel status to our status field
                lionwheel_status = result.get('status')
                if lionwheel_status is not None:
                    # Map LionWheel status codes to our selection values
                    status_mapping = {
                        0: '1',  # UNASSIGNED -> Open
                        1: '2',  # ASSIGNED -> Transferred to courier
                        2: '2',  # ACTIVE -> Transferred to courier
                        3: '3',  # COMPLETED -> Done
                        4: '8',  # CANCELED -> Cancelled
                        5: '3',  # ROUNDTRIP_DELIVERED -> Done
                        8: '8',  # FAILED -> Cancelled
                    }
                    self.shipment_status = status_mapping.get(lionwheel_status, '1')
                
                return result
            else:
                print(f"Request failed with status code: {response.status_code}")
                print(f"Response body: {response.text}")
                raise UserError(_(f"LionWheel API request failed: {response.status_code} - {response.text}"))
                
        except requests.exceptions.RequestException as e:
            print(f"Request error: {e}")
            raise UserError(_(f"LionWheel API request error: {str(e)}"))

    def action_update_shipment_status(self, new_status=None):
        """Update shipment status using LionWheel API PUT method"""
        print("action_update_shipment_status")
        
        if not self.carrier_id:
            raise UserError(_('Please select a delivery carrier.'))
        
        api_key = self.carrier_id.lionwheel_api_key
        api_url = self.carrier_id.lionwheel_api_url or "https://members.lionwheel.com/api/v1"
        
        if not api_key:
            raise UserError(_('LionWheel API key not configured. Please set it in the delivery carrier settings.'))
        
        if not self.carrier_tracking_ref:
            raise UserError(_('No tracking reference found. Please create a shipment first.'))
        
        # Build URL for updating task
        url_with_key = f"{api_url}/tasks/{self.carrier_tracking_ref}/update?key={api_key}"
        
        headers = {
            "Content-Type": "application/json"
        }

        # Prepare update payload
        update_payload = {}
        
        if new_status is not None:
            # Map our status to LionWheel status codes
            status_mapping = {
                '1': 0,  # Open -> UNASSIGNED
                '2': 1,  # Transferred to courier -> ASSIGNED
                '3': 3,  # Done -> COMPLETED
                '8': 4,  # Cancelled -> CANCELED
            }
            update_payload['status'] = status_mapping.get(new_status, 0)
        
        # Add pickup date if needed
        if not update_payload.get('pickup_at'):
            update_payload['pickup_at'] = datetime.now().strftime("%d/%m/%Y")

        payload_json = json.dumps(update_payload)
        print(f"Update payload: {payload_json}")

        try:
            response = requests.put(url_with_key, headers=headers, data=payload_json)
            print(f"Response Status: {response.status_code}")

            if response.status_code == 200:
                result = response.json()
                print("Success! Response:")
                print(json.dumps(result, indent=2))
                
                # Update our status field
                if new_status:
                    self.shipment_status = new_status
                
                return result
            else:
                print(f"Request failed with status code: {response.status_code}")
                print(f"Response body: {response.text}")
                raise UserError(_(f"LionWheel API request failed: {response.status_code} - {response.text}"))
                
        except requests.exceptions.RequestException as e:
            print(f"Request error: {e}")
            raise UserError(_(f"LionWheel API request error: {str(e)}"))

    def action_add_document_to_shipment(self, file_content=None, file_name=None):
        """Add document to shipment using LionWheel API"""
        print("action_add_document_to_shipment")
        
        if not self.carrier_id:
            raise UserError(_('Please select a delivery carrier.'))
        
        api_key = self.carrier_id.lionwheel_api_key
        api_url = self.carrier_id.lionwheel_api_url or "https://members.lionwheel.com/api/v1"
        
        if not api_key:
            raise UserError(_('LionWheel API key not configured. Please set it in the delivery carrier settings.'))
        
        if not self.carrier_tracking_ref:
            raise UserError(_('No tracking reference found. Please create a shipment first.'))
        
        # Build URL for adding document
        url_with_key = f"{api_url}/tasks/{self.carrier_tracking_ref}/add_document?key={api_key}"
        
        headers = {
            "Content-Type": "application/json"
        }

        # Prepare document payload
        if file_content:
            import base64
            file_base64 = base64.b64encode(file_content).decode('utf-8')
            payload = {
                "file": file_base64
            }
        else:
            # For now, we'll create a simple text document
            import base64
            document_content = f"Shipment {self.carrier_tracking_ref} created on {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}"
            file_base64 = base64.b64encode(document_content.encode('utf-8')).decode('utf-8')
            payload = {
                "file": file_base64
            }

        payload_json = json.dumps(payload)
        print(f"Document payload length: {len(payload_json)}")

        try:
            response = requests.post(url_with_key, headers=headers, data=payload_json)
            print(f"Response Status: {response.status_code}")

            if response.status_code == 200:
                result = response.json()
                print("Success! Document added:")
                print(json.dumps(result, indent=2))
                return result
            else:
                print(f"Request failed with status code: {response.status_code}")
                print(f"Response body: {response.text}")
                raise UserError(_(f"LionWheel API request failed: {response.status_code} - {response.text}"))
                
        except requests.exceptions.RequestException as e:
            print(f"Request error: {e}")
            raise UserError(_(f"LionWheel API request error: {str(e)}"))

    def action_get_daily_route(self, driver_id=None, route_date=None):
        """Get daily route information using LionWheel API"""
        print("action_get_daily_route")
        
        if not self.carrier_id:
            raise UserError(_('Please select a delivery carrier.'))
        
        api_key = self.carrier_id.lionwheel_api_key
        api_url = self.carrier_id.lionwheel_api_url or "https://members.lionwheel.com/api/v1"
        
        if not api_key:
            raise UserError(_('LionWheel API key not configured. Please set it in the delivery carrier settings.'))
        
        # Use provided driver_id or default to 1
        driver_id = driver_id or 1
        
        # Use provided date or default to today
        if not route_date:
            route_date = datetime.now().strftime("%d/%m/%Y")
        
        # Build URL for getting daily route with query parameters
        url_with_key = f"{api_url}/drivers/{driver_id}/daily_route?key={api_key}&date={route_date}"
        
        headers = {
            "Content-Type": "application/json"
        }

        try:
            response = requests.get(url_with_key, headers=headers)
            print(f"Response Status: {response.status_code}")

            if response.status_code == 200:
                result = response.json()
                print("Success! Daily route:")
                print(json.dumps(result, indent=2))
                return result
            else:
                print(f"Request failed with status code: {response.status_code}")
                print(f"Response body: {response.text}")
                raise UserError(_(f"LionWheel API request failed: {response.status_code} - {response.text}"))
                
        except requests.exceptions.RequestException as e:
            print(f"Request error: {e}")
            raise UserError(_(f"LionWheel API request error: {str(e)}"))

    def action_optimize_daily_route(self, driver_id=None, route_date=None):
        """Optimize daily route using LionWheel API"""
        print("action_optimize_daily_route")
        
        if not self.carrier_id:
            raise UserError(_('Please select a delivery carrier.'))
        
        api_key = self.carrier_id.lionwheel_api_key
        api_url = self.carrier_id.lionwheel_api_url or "https://members.lionwheel.com/api/v1"
        
        if not api_key:
            raise UserError(_('LionWheel API key not configured. Please set it in the delivery carrier settings.'))
        
        # Use provided driver_id or default to 1
        driver_id = driver_id or 1
        
        # Use provided date or default to today
        if not route_date:
            route_date = datetime.now().strftime("%d/%m/%Y")
        
        # Build URL for optimizing daily route
        url_with_key = f"{api_url}/drivers/{driver_id}/optimize_daily_route?key={api_key}"
        
        headers = {
            "Content-Type": "application/json"
        }

        # Prepare payload
        payload = {
            "date": route_date
        }

        payload_json = json.dumps(payload)
        print(f"Optimize route payload: {payload_json}")

        try:
            response = requests.post(url_with_key, headers=headers, data=payload_json)
            print(f"Response Status: {response.status_code}")

            if response.status_code == 200:
                result = response.json()
                print("Success! Route optimized:")
                print(json.dumps(result, indent=2))
                return result
            else:
                print(f"Request failed with status code: {response.status_code}")
                print(f"Response body: {response.text}")
                raise UserError(_(f"LionWheel API request failed: {response.status_code} - {response.text}"))
                
        except requests.exceptions.RequestException as e:
            print(f"Request error: {e}")
            raise UserError(_(f"LionWheel API request error: {str(e)}"))

    def action_get_company_details(self, company_id=None):
        """Get company details using LionWheel API"""
        print("action_get_company_details")
        
        if not self.carrier_id:
            raise UserError(_('Please select a delivery carrier.'))
        
        # For company details, we need the org_key (organization key)
        # This should be configured separately in the carrier settings
        org_key = self.carrier_id.lionwheel_org_key or self.carrier_id.lionwheel_api_key
        api_url = self.carrier_id.lionwheel_api_url or "https://members.lionwheel.com/api/v1"
        
        if not org_key:
            raise UserError(_('LionWheel Organization key not configured. Please set it in the delivery carrier settings.'))
        
        # Use provided company_id or get from carrier settings
        company_id = company_id or self.carrier_id.lionwheel_company_id
        
        if not company_id:
            raise UserError(_('Company ID not configured. Please set it in the delivery carrier settings.'))
        
        # Build URL for getting company details with org_key
        url_with_key = f"{api_url}/companies/{company_id}?key={org_key}"
        
        headers = {
            "Content-Type": "application/json"
        }

        try:
            response = requests.get(url_with_key, headers=headers)
            print(f"Response Status: {response.status_code}")

            if response.status_code == 200:
                result = response.json()
                print("Success! Company details:")
                print(json.dumps(result, indent=2))
                return result
            else:
                print(f"Request failed with status code: {response.status_code}")
                print(f"Response body: {response.text}")
                raise UserError(_(f"LionWheel API request failed: {response.status_code} - {response.text}"))
                
        except requests.exceptions.RequestException as e:
            print(f"Request error: {e}")
            raise UserError(_(f"LionWheel API request error: {str(e)}"))

    def action_list_routes(self, route_date=None, format_type='json'):
        """List routes using LionWheel API"""
        print("action_list_routes")
        
        if not self.carrier_id:
            raise UserError(_('Please select a delivery carrier.'))
        
        api_key = self.carrier_id.lionwheel_api_key
        api_url = self.carrier_id.lionwheel_api_url or "https://members.lionwheel.com/api/v1"
        
        if not api_key:
            raise UserError(_('LionWheel API key not configured. Please set it in the delivery carrier settings.'))
        
        # Use provided date or default to today
        if not route_date:
            route_date = datetime.now().strftime("%d/%m/%Y")
        
        # Build URL for listing routes with query parameters
        url_with_key = f"{api_url}/routes?key={api_key}&date={route_date}&format={format_type}"
        
        headers = {
            "Content-Type": "application/json"
        }

        try:
            response = requests.get(url_with_key, headers=headers)
            print(f"Response Status: {response.status_code}")

            if response.status_code == 200:
                if format_type == 'json':
                    result = response.json()
                else:
                    result = response.text
                print("Success! Routes list:")
                print(result)
                return result
            else:
                print(f"Request failed with status code: {response.status_code}")
                print(f"Response body: {response.text}")
                raise UserError(_(f"LionWheel API request failed: {response.status_code} - {response.text}"))
                
        except requests.exceptions.RequestException as e:
            print(f"Request error: {e}")
            raise UserError(_(f"LionWheel API request error: {str(e)}"))

    def generate_shipment_label(self):
        print("generate_shipment_label")
        
        if not self.carrier_id:
            raise UserError(_('Please select a delivery carrier.'))
        
        api_key = self.carrier_id.lionwheel_api_key
        api_url = self.carrier_id.lionwheel_api_url or "https://members.lionwheel.com/api/v1"
        
        if not api_key:
            raise UserError(_('LionWheel API key not configured. Please set it in the delivery carrier settings.'))
        
        if not self.carrier_tracking_ref:
            raise UserError(_('No tracking reference found. Please create a shipment first.'))
        
        # Build URL for getting task details (which may include label/link)
        url_with_key = f"{api_url}/tasks/{self.carrier_tracking_ref}?key={api_key}"
        
        headers = {
            "Content-Type": "application/json"
        }

        try:
            response = requests.get(url_with_key, headers=headers)
            print(f"Response Status: {response.status_code}")

            if response.status_code == 200:
                result = response.json()
                print("Success! Response:")
                print(json.dumps(result, indent=2))

                # LionWheel may provide a link to the task or label
                # This depends on how LionWheel provides labels
                task_link = result.get("link") or result.get("url")
                if task_link:
                    self.waybill_link = task_link
                else:
                    # If no direct link, we can construct one to the LionWheel dashboard
                    base_url = api_url.replace("/api/v1", "")
                    self.waybill_link = f"{base_url}/tasks/{self.carrier_tracking_ref}"
                
                return result
            else:
                print(f"Request failed with status code: {response.status_code}")
                print(f"Response body: {response.text}")
                raise UserError(_(f"LionWheel API request failed: {response.status_code} - {response.text}"))
                
        except requests.exceptions.RequestException as e:
            print(f"Request error: {e}")
            raise UserError(_(f"LionWheel API request error: {str(e)}"))

    def action_create_company(self, company_data=None):
        """Create company using LionWheel API"""
        print("action_create_company")
        
        if not self.carrier_id:
            raise UserError(_('Please select a delivery carrier.'))
        
        # For company operations, we need the org_key
        org_key = self.carrier_id.lionwheel_org_key or self.carrier_id.lionwheel_api_key
        api_url = self.carrier_id.lionwheel_api_url or "https://members.lionwheel.com/api/v1"
        
        if not org_key:
            raise UserError(_('LionWheel Organization key not configured. Please set it in the delivery carrier settings.'))
        
        # Build URL for creating company
        url_with_key = f"{api_url}/companies?key={org_key}"
        
        headers = {
            "Content-Type": "application/json"
        }

        # Prepare company payload
        if company_data:
            payload = company_data
        else:
            # Default company data
            payload = {
                "name": "New Company",
                "legal_id": "",
                "primary_email": "",
                "office_phone": "",
                "cell_phone": "",
                "default_earliest_at": "09:00",
                "default_latest_at": "18:00",
                "is_active": True,
                "default_location_attributes": {
                    "name": "Default Location",
                    "city": "Tel Aviv",
                    "street": "Main Street",
                    "number": "1",
                    "zip_code": "",
                    "default_recipient_name": "Contact Person",
                    "default_phone": "",
                    "default_email": ""
                }
            }

        payload_json = json.dumps(payload)
        print(f"Create company payload: {payload_json}")

        try:
            response = requests.post(url_with_key, headers=headers, data=payload_json)
            print(f"Response Status: {response.status_code}")

            if response.status_code == 200:
                result = response.json()
                print("Success! Company created:")
                print(json.dumps(result, indent=2))
                return result
            else:
                print(f"Request failed with status code: {response.status_code}")
                print(f"Response body: {response.text}")
                raise UserError(_(f"LionWheel API request failed: {response.status_code} - {response.text}"))
                
        except requests.exceptions.RequestException as e:
            print(f"Request error: {e}")
            raise UserError(_(f"LionWheel API request error: {str(e)}"))

    def action_update_company(self, company_id=None, company_data=None):
        """Update company using LionWheel API"""
        print("action_update_company")
        
        if not self.carrier_id:
            raise UserError(_('Please select a delivery carrier.'))
        
        # For company operations, we need the org_key
        org_key = self.carrier_id.lionwheel_org_key or self.carrier_id.lionwheel_api_key
        api_url = self.carrier_id.lionwheel_api_url or "https://members.lionwheel.com/api/v1"
        
        if not org_key:
            raise UserError(_('LionWheel Organization key not configured. Please set it in the delivery carrier settings.'))
        
        # Use provided company_id or get from carrier settings
        company_id = company_id or self.carrier_id.lionwheel_company_id
        
        if not company_id:
            raise UserError(_('Company ID not configured. Please set it in the delivery carrier settings.'))
        
        # Build URL for updating company
        url_with_key = f"{api_url}/companies/{company_id}?key={org_key}"
        
        headers = {
            "Content-Type": "application/json"
        }

        # Prepare company update payload
        if company_data:
            payload = company_data
        else:
            # Default update data
            payload = {
                "name": "Updated Company Name",
                "is_active": True
            }

        payload_json = json.dumps(payload)
        print(f"Update company payload: {payload_json}")

        try:
            response = requests.patch(url_with_key, headers=headers, data=payload_json)
            print(f"Response Status: {response.status_code}")

            if response.status_code == 200:
                result = response.json()
                print("Success! Company updated:")
                print(json.dumps(result, indent=2))
                return result
            else:
                print(f"Request failed with status code: {response.status_code}")
                print(f"Response body: {response.text}")
                raise UserError(_(f"LionWheel API request failed: {response.status_code} - {response.text}"))
                
        except requests.exceptions.RequestException as e:
            print(f"Request error: {e}")
            raise UserError(_(f"LionWheel API request error: {str(e)}"))
