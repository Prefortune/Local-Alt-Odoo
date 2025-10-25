from odoo import http
from odoo.http import request
import stripe
import logging
import re
from odoo.http import Response
_logger = logging.getLogger(__name__)
import werkzeug
class SponsorshipController(http.Controller):

    @http.route(['/sponsorship/apply/<int:sponsorship_id>'], type='http', auth='public', website=True)

    def apply_sponsorship(self, sponsorship_id, **kw):

        _logger.info(f"Applying sponsorship for sponsorship_id: {sponsorship_id}")
        # Set your Stripe API key
        stripe.api_key = request.env['ir.config_parameter'].sudo().get_param('pf_event_sponsorship.stripe_secret_key')
        _logger.info(f"Stripe API Key: {stripe.api_key}")
        # stripe.api_key = 'sk_test_51RDlVEHIc2T5D1fBPMw0JXTrNhcMql4HMb4R52xZPGnF8PTvJsSoPoTiiQfhkHS3Mraqz2faEZ6jcOhMa2wPeIpG004YHK4pVB'

        secret_key = request.env['ir.config_parameter'].sudo().get_param('pf_event_sponsorship.stripe_secret_key')
        
        # Validate the key
        try:
            stripe.api_key = secret_key
            stripe.Account.retrieve()

        except stripe.error.AuthenticationError:
                    return request.render("pf_event_sponsorship.my_error_template", {
                                    'error_message': "Invalid Stripe Secret Key. Please contact the administrator."})

        sponsorship = request.env['event.sponsorship'].sudo().browse(sponsorship_id)

        if not sponsorship.exists():
            return request.not_found()
        
        def get_or_create_product_price_currency(product_name, currency, price_in_cents):
           
            products = stripe.Product.search(query=f"name:'{product_name}'", limit=1)

            product = None
            if products.data:
                existing_product = products.data[0]
                if existing_product.active:
                    product = existing_product

            # If no active product found, create a new one
            if not product:
                product = stripe.Product.create(name=product_name, active=True)

          
            matching_price = None
            prices = stripe.Price.list(product=product.id)
            for p in prices.auto_paging_iter():
                if p.currency == currency.lower() and p.unit_amount == price_in_cents:
                    matching_price = p
                    break

           
            if not matching_price:
                matching_price = stripe.Price.create(
                    unit_amount=price_in_cents,
                    currency=currency.lower(),
                    product=product.id
                )

            return product, matching_price


        sponsorship_amount_in_cents = int(sponsorship.sponsorship_amount * 100)
        event_name = re.sub(r'[^\w\s-]', '', sponsorship.event_id.name).strip()
        sponsorship_type = sponsorship.get_sponsorship_type_display()
        product_name = f"Sponsorship - {event_name} - {sponsorship_type}"

        product, price = get_or_create_product_price_currency(
                product_name,
                sponsorship.currency_id.name.lower(),
                sponsorship_amount_in_cents
            )

        session = stripe.checkout.Session.create(
                success_url=request.httprequest.host_url + f'payment/success?session_id={{CHECKOUT_SESSION_ID}}',
                cancel_url=request.httprequest.host_url + 'payment/cancel',
                mode="payment",
                # billing_address_collection='required',
                # payment_intent_data={
                #     'capture_method': 'automatic',
                # },
                phone_number_collection= {
                    "enabled": True,
                },
                line_items=[{
                    'price': price.id,
                    'quantity': 1,
                }],
                metadata={
                    'event_id': str(sponsorship.event_id.id),
                    'sponsorship_id': str(sponsorship.id),
                    'phone_number': kw.get('phone_number', 'N/A'),
                }
            )
            
        _logger.info(f"Stripe session created: {session.id}")
        _logger.info(f"Stripe session URL: {session.url}")
        return werkzeug.utils.redirect(session.url)


class PaymentFeedbackController(http.Controller):

    @http.route('/payment/success', type='http', auth='public')
    def payment_success(self, **kw):
        session_id = kw.get('session_id')
        # sponsorship_id = kw.get('sponsorship_id')
        # stripe.api_key = 'sk_test_51RDlVEHIc2T5D1fBPMw0JXTrNhcMql4HMb4R52xZPGnF8PTvJsSoPoTiiQfhkHS3Mraqz2faEZ6jcOhMa2wPeIpG004YHK4pVB'
        stripe.api_key = request.env['ir.config_parameter'].sudo().get_param('pf_event_sponsorship.stripe_secret_key')
        
        try:
            if not session_id :
                return "<h3>Error: Session ID not provided.</h3>"

            

            session = stripe.checkout.Session.retrieve(
                session_id,
               
            )
            _logger.info(f"Stripe session retrieved: {session}")
        
           
          


            if not session:
                return "<h3>Error: Stripe session not found.</h3>"
            


           

            metadata = session.get('metadata', {})
            event_id = metadata.get('event_id')
            sponsorship_id_meta = metadata.get('sponsorship_id')

            sponsorship = request.env['event.sponsorship'].sudo().browse(int(sponsorship_id_meta))

            if not sponsorship.exists():
                return "<h3>Error: Sponsorship record not found.</h3>"

            if not event_id or not sponsorship_id_meta:
                return "<h3>Error: Missing metadata in Stripe session.</h3>"
            

            msg= f"""
            <script type="text/javascript">
                if (window.self !== window.top) {{
                    window.top.location = window.self.location;
                }}
            </script>
    
            <div style="max-width: 800px; margin: 0 auto; padding: 30px;">
                <h2 style="text-align: center; color: #28a745; font-size: 32px; margin-bottom: 5px;">
                    🎉 Thank You!
                </h2>
                <p style="text-align: center; color: #6c757d; margin-bottom: 25px;">
                    Your sponsorship has been received successfully.
                </p>

                <div style="border: 1px solid #dee2e6; border-radius: 8px; overflow: hidden; box-shadow: 0 0 12px rgba(0,0,0,0.05);">
                    <div style= "background-color: #f8f9fa;padding: 16px 20px; font-weight: 600; font-size: 16px; align-items: center;">
                                
                                <div style="margin-bottom:20px">
                                    <span style="margin-right: 8px;font-size: 25px">💳 Payment Details</span> 
                                </div>
                                <table style="width: 100%;font-size: 15px;border: 1px solid #e9ecef;border-collapse: collapse; margin-bottom: 5px;">
                                    <tr>
                                        <td style="padding: 12px;border: 1px solid #e9ecef;border-collapse: collapse;"><strong>Name</strong></td>
                                        <td style="padding: 12px;border: 1px solid #e9ecef;border-collapse: collapse;">{session.customer_details.name}</td>
                                    </tr>
                                    <tr >
                                        <td style="padding: 12px; border: 1px solid #e9ecef;border-collapse: collapse;"><strong>Phone Number</strong></td>
                                        <td style="padding: 12px; border: 1px solid #e9ecef;border-collapse: collapse;">{session.customer_details.phone}</td>
                                    </tr>
                                    <tr border: 1px solid #e9ecef;>
                                        <td style="padding: 12px; border: 1px solid #e9ecef;border-collapse: collapse;"><strong>Email</strong></td>
                                        <td style="padding: 12px; border: 1px solid #e9ecef;border-collapse: collapse;">{session.customer_details.email}</td>
                                    </tr>
                                    <tr>
                                        <td style="padding: 12px; border: 1px solid #e9ecef;border-collapse: collapse;"><strong>Status</strong></td>
                                        <td style="padding: 12px; border: 1px solid #e9ecef;border-collapse: collapse;">
                                            <span style="background-color: #28a745; color: white; padding: 4px 12px; border-radius: 12px; font-size: 13px;">
                                                {session.payment_status.capitalize()}
                                            </span>
                                        </td>
                                    </tr>
                                    <tr>
                                        <td style="padding: 12px; border: 1px solid #e9ecef;border-collapse: collapse;"><strong>Payment Ref</strong></td>
                                        <td style="padding: 12px; border: 1px solid #e9ecef;border-collapse: collapse;">{session.id}</td>
                                    </tr>
                                    <tr>
                                        <td style="padding: 12px; border: 1px solid #e9ecef;border-collapse: collapse;"><strong>Sponsorship</strong></td>
                                        <td style="padding: 12px; border: 1px solid #e9ecef;border-collapse: collapse;">{sponsorship.get_sponsorship_type_display()}</td>
                                    </tr>
                                    <tr>
                                        <td style="padding: 12px;border: 1px solid #e9ecef;border-collapse: collapse;"><strong>Event</strong></td>
                                        <td style="padding: 12px;border: 1px solid #e9ecef;border-collapse: collapse;">{sponsorship.event_id.name}</td>
                                    </tr>
                                </table>
                            
                            <div style="text-align: center; margin-bottom: 0px;">
                                <button onclick="window.location.href='/events'" style="background-color: #6f42c1; color: white; padding: 10px 25px; text-decoration: none; border: none; border-radius: 6px; font-weight: bold; cursor: pointer;">
                                     ⬅ Back to Events
                                </button>
                     </div>
                </div>
            </div>

            """
            
            existing = request.env['sponsorship.payment.session'].sudo().search([('session_id', '=', session_id)], limit=1)
            if existing :
                 return Response(msg)
            else:
                _logger.info(f"Creating new sponsorship payment session record for session ID: {session_id}")
                payment_session= request.env['sponsorship.payment.session'].sudo().create({
                    'event_id': int(event_id),
                    'sponsorship_id': int(sponsorship_id_meta),
                    'session_id': session.id,
                    'name': session.customer_details.name,
                    'customer_email': session.customer_details.email,
                    'sponsorship_type': sponsorship.get_sponsorship_type_display(),
                    'amount_total': session.amount_total / 100,
                    'payment_status': session.payment_status,
                    'currency': session.currency.upper(),
                    'phone': session.customer_details.phone,
                })

                if session.payment_status == 'paid' and sponsorship.event_id.user_id.email: 
                    template = request.env.ref('pf_event_sponsorship.email_template_sponsorship_payment_succesfully', raise_if_not_found=False)
                    if template:
                        template.sudo().send_mail(
                            payment_session.id,
                            force_send=True,
                            email_values={
                                'email_to': sponsorship.event_id.user_id.email,
                                'email_from': request.env.company.email or 'noreply@yourcompany.com',
                            }
                        )
                        _logger.info(f"Email sent to {sponsorship.event_id.user_id.email} for sponsorship payment {session.id}")
                    else:
                        _logger.warning("Email template 'email_template_sponsorship_payment_succesfully' not found")
                else:
                    _logger.warning(f"Email not sent: Payment status is '{session.payment_status}' or no responsible person email found for event {event_id}")


                if session.payment_status == 'paid' and payment_session.customer_email: 
                    template = request.env.ref('pf_event_sponsorship.email_template_sponsorship_payment_succesfully_sponsor', raise_if_not_found=False)
                    if template:
                        template.sudo().send_mail(
                            payment_session.id,
                            force_send=True,
                            email_values={
                                'email_to': payment_session.customer_email,
                                'email_from': request.env.company.email or 'noreply@yourcompany.com',
                            }
                        )
                        _logger.info(f"Email sent to {payment_session.customer_email} for sponsorship payment {session.id}")
                    else:
                        _logger.warning("Email template 'email_template_sponsorship_payment_succesfully_sponsor' not found")
                else:
                    _logger.warning(f"Email not sent: Payment status is '{session.payment_status}' or no Customer Email id found {payment_session.customer_email}")
                return Response(msg)
        except Exception as e:
            _logger.error(f"Stripe payment success error: {str(e)}")
            return f"<h3>Error retrieving payment session: {e}</h3>"
        

