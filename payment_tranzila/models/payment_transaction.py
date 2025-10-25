# -*- coding: utf-8 -*-

from werkzeug import urls
from odoo import _, api, models
from odoo.exceptions import ValidationError
from odoo.addons.payment import utils as payment_utils
from odoo.addons.payment_tranzila.controllers.main import TranzilaController
import requests
import pprint
import logging
import json
_logger = logging.getLogger(__name__)

class PaymentTransaction(models.Model):
    def _send_payment_request(self):
        """ Override of payment to send a payment request to Tranzila with a confirmed PaymentToken.

        Note: self.ensure_one()

        :return: None
        :raise: UserError if the transaction is not linked to a token
        """
        super()._send_payment_request()
        if self.provider_code != 'tranzila':
            return
        api_url = 'https://secure5.tranzila.com/cgi-bin/tranzila71u.cgi'
        headersList = {
            "Content-Type": "application/x-www-form-urlencoded"
        }
        payload = {
            'supplier': self.provider_id.token_supplier,
            'TranzilaPW': self.provider_id.token_tranzilaPW,
            'TranzilaTK': self.token_id.provider_ref,
            'sum': self.amount,
            'expdate': self.token_id.expmonth + self.token_id.expyear,
            'reference': self.reference,
            'response_return_format': 'json'
        }
        response = requests.request("POST", api_url, data=payload, headers=headersList)
        feedback_data = {'response': response.text}
        _logger.info("entering _handle_feedback_data with data:\n%s", pprint.pformat(feedback_data))
        self._handle_notification_data('tranzila', feedback_data)

    _inherit = 'payment.transaction'


    def _get_specific_rendering_values(self, processing_values):
        """ Override of payment to return Tranzila-specific rendering values.

        Note: self.ensure_one() from `_get_processing_values`

        :param dict processing_values: The generic and specific processing values of the transaction
        :return: The dict of provider-specific processing values
        :rtype: dict
        """
        res = super()._get_specific_rendering_values(processing_values)
        partner = self.partner_id
        mobile = partner.mobile or partner.phone
        if self.provider_code != 'tranzila':
            return res
        if self.tokenize:
            api_url = 'https://direct.tranzila.com/' + self.provider_id.token_supplier + '/iframenew.php?sum=%s&currency=%s&lang=il&contact=%s&phone=%s' % (
                self.amount, 1, partner.name, mobile) + '&tranmode=VK&u71=1'
        else:
            api_url = 'https://direct.tranzila.com/' + self.provider_id.supplier + '/iframenew.php?sum=%s&currency=%s&lang=il&contact=%s&phone=%s' % (
            self.amount, 1, partner.name, mobile)
        tranzila_values = {
            'return_url': urls.url_join(self.get_base_url(),
                                        TranzilaController._return_url),
            'api_url': api_url,
            'reference': self.reference
        }
        return tranzila_values

    @api.model
    def _get_tx_from_notification_data(self, provider_code, notification_data):
        """ Override of payment to find the transaction based on Tranzila data.

        :param str provider_code: The provider of the provider that handled the transaction
        :param dict notification_data: The feedback data sent by the provider
        :return: The transaction if found
        """
        tx = super()._get_tx_from_notification_data(provider_code, notification_data)
        _logger.info("Response Data with data:\n%s", pprint.pformat(notification_data))
        if provider_code != 'tranzila':
            return tx
        if 'response' in notification_data:
            data_vals = notification_data.get('response')
            data_vals = json.loads(data_vals)
            reference = data_vals.get('reference')
        else:
            reference = notification_data.get('reference')
        if not reference:
            raise ValidationError(
                "Tranzila: " + _(
                    "Received data with missing reference (%(ref)s)",
                    ref=reference,
                )
            )
        tx = self.search([('reference', '=', reference), ('provider_code', '=', 'tranzila')])
        if not tx:
            raise ValidationError(
                "Tranzila: " + _("No transaction found matching reference %s.", reference)
            )
        return tx

    # Global dictionary of error codes and messages
    ERROR_MESSAGES = {
        "000": {
            "en": "Transaction approved",
            "he": "העסקה אושרה"
        },
        "001": {
            "en": "Blocked confiscate card.",
            "he": "חסום, להחרים כרטיס."
        },
        "002": {
            "en": "Stolen confiscate card.",
            "he": "גנוב, להחרים כרטיס."
        },
        "003": {
            "en": "Contact credit company.",
            "he": "צור קשר עם חברת האשראי."
        },
        "004": {
            "en": "Refusal.",
            "he": "סירוב."
        },
        "005": {
            "en": "Forged. confiscate card.",
            "he": "מזויף, להחרים כרטיס."
        },
        "006": {
            "en": "Identity Number of CVV incorrect.",
            "he": "מספר תעודת זהות או CVV שגויים."
        },
        "007": {
            "en": "Must contact Credit Card Company.",
            "he": "חובה ליצור קשר עם חברת האשראי."
        },
        "008": {
            "en": "Fault in building of access key to blocked cards file.",
            "he": "שגיאה בבניית מפתח גישה לקובץ כרטיסים חסומים."
        },
        "009": {
            "en": "Contact unsuccessful.",
            "he": "ניסיון ליצור קשר נכשל."
        },
        "010": {
            "en": "Program ceased by user instruction (ESC).",
            "he": "התוכנית הופסקה בהוראת המשתמש (ESC)."
        },
        "011": {
            "en": "No confirmation for the ISO currency clearing.",
            "he": "אין אישור למטבע ISO של העסקה."
        },
        "012": {
            "en": "No confirmation for the ISO currency type.",
            "he": "אין אישור לסוג מטבע ISO."
        },
        "013": {
            "en": "No confirmation for charge/discharge transaction.",
            "he": "אין אישור לפעולת חיוב/זיכוי."
        },
        "014": {
            "en": "Unsupported card.",
            "he": "כרטיס לא נתמך."
        },
        "015": {
            "en": "Number Entered and Magnetic Strip do not match.",
            "he": "מספר שהוזן ורצועה מגנטית לא תואמים."
        },
        "017": {
            "en": "Last 4 digits not entered.",
            "he": "4 הספרות האחרונות לא הוזנו."
        },
        "019": {
            "en": "Record in INT_IN shorter than 16 characters.",
            "he": "רישום ב-INT_IN קצר מ-16 תווים."
        },
        "020": {
            "en": "Input file (INT_IN) does not exist.",
            "he": "קובץ קלט (INT_IN) לא קיים."
        },
        "021": {
            "en": "Blocked cards file (NEG) non-existent or has not been "
                  "updated - execute transmission or request authorization "
                  "for each transaction.",
            "he": "קובץ כרטיסים חסומים (NEG)"
                  " אינו קיים או לא עודכן - בצע שידור או בקש אישור לכל עסקה."
        },
        "022": {
            "en": "One of the parameter files or vectors do not exist.",
            "he": "אחד מקבצי הפרמטרים או הוקטורים לא קיים."
        },
        "023": {
            "en": "Date file (DATA) does not exist.",
            "he": "קובץ תאריך (DATA) לא קיים."
        },
        "024": {
            "en": "Format file (START) does not exist.",
            "he": "קובץ פורמט (START) לא קיים."
        },
        "025": {
            "en": "Difference in days in input of blocked cards is too "
                  "large - execute transmission or request authorization for "
                  "each transaction.",
            "he": "הבדל בימים בקלט"
                  " כרטיסים חסומים גדול מדי - בצע שידור או בקש אישור לכל עסקה."
        },
        "026": {
            "en": "Difference in generations in input of blocked cards is too "
                  "large - execute transmission or request authorization for "
                  "each transaction.",
            "he": "הבדל בדורות בקלט"
                  " כרטיסים חסומים גדול מדי - בצע שידור או בקש אישור לכל עסקה."
        },
        "027": {
            "en": "Where the magnetic strip is not completely entered.",
            "he": "רצועה מגנטית לא הוזנה במלואה."
        },
        "028": {
            "en": "Central terminal number not entered into terminal defined "
                  "for work as main supplier.",
            "he": "מספר מסוף מרכזי לא הוזן למסוף המוגדר כספק ראשי."
        },
        "029": {
            "en": "Beneficiary number not entered into terminal defined as "
                  "main beneficiary.",
            "he": "מספר מוטב לא הוזן למסוף המוגדר כמוטב ראשי."
        },
        "030": {
            "en": "Terminal not updated as main supplier/beneficiary and "
                  "supplier/beneficiary number entered.",
            "he": "מסוף לא עודכן כספק/מוטב ראשי והוזן מספר ספק/מוטב."
        },
        "031": {
            "en": "Terminal updated as main supplier and beneficiary "
                  "number entered.",
            "he": "מסוף עודכן כספק ראשי והוזן מספר מוטב."
        },
        "032": {
            "en": "Old transactions - carry out transmission or request "
                  "authorization for each transaction.",
            "he": "עסקאות ישנות - בצע שידור או בקש אישור לכל עסקה."
        },
        "033": {
            "en": "Defective card.",
            "he": "כרטיס פגום."
        },
        "034": {
            "en": "Card not permitted for this terminal or no authorization "
                  "for this type of transaction.",
            "he": "כרטיס לא מורשה למסוף זה או אין אישור לסוג זה של עסקה."
        },
        "035": {
            "en": "Card not permitted for transaction or type of credit.",
            "he": "כרטיס לא מורשה לעסקה או לסוג אשראי זה."
        },
        "036": {
            "en": "Expired.",
            "he": "פג תוקף."
        },
        "037": {
            "en": "Error in instalments - Amount of transaction needs to be "
                  "equal to the first instalment + (fixed instalments times "
                  "no. of instalments).",
            "he": "שגיאה בתשלומים - סכום העסקה צריך להיות"
                  " שווה לתשלום הראשון + (תשלומים קבועים כפול מספר התשלומים)."
        },
        "038": {
            "en": "Cannot execute transaction in excess of credit card "
                  "ceiling for immediate debit.",
            "he": "לא ניתן לבצע עסקה העולה על תקרת האשראי להחיוב המיידי."
        },
        "039": {
            "en": "Control number incorrect.",
            "he": "מספר ביקורת שגוי."
        },
        "040": {
            "en": "Terminal defined as main beneficiary and supplier "
                  "number entered.",
            "he": "מסוף מוגדר כמוטב ראשי והוזן מספר ספק."
        },
        "041": {
            "en": "Exceeds ceiling where input file contains J1 or J2 or J3 "
                  "(contact prohibited).",
            "he": "חורג"
                  " מהתקרה בקובץ קלט המכיל J1 או J2 או J3 (אסור ליצור קשר)."
        },
        "042": {
            "en": "Card blocked for supplier where input file contains J1 or "
                  "J2 or J3 (contact prohibited).",
            "he": "כרטיס חסום"
                  " לספק בקובץ קלט המכיל J1 או J2 או J3 (אסור ליצור קשר)."
        },
        "043": {
            "en": "Random where input file contains J1 (contact prohibited).",
            "he": "אקראי בקובץ קלט המכיל J1 (אסור ליצור קשר)."
        },
        "044": {
            "en": "Terminal prohibited from requesting authorization without "
                  "transaction (J5).",
            "he": "מסוף אסור לבקש אישור ללא עסקה (J5)."
        },
        "045": {
            "en": "Terminal prohibited for supplier-initiated authorization "
                  "request (J6).",
            "he": "מסוף אסור לבקשת אישור יזומה על ידי הספק (J6)."
        },
        "046": {
            "en": "Terminal must request authorization where input file "
                  "contains J1 or J2 or J3 (contact prohibited).",
            "he": "מסוף חייב לבקש אישור"
                  " בקובץ קלט המכיל J1 או J2 או J3 (אסור ליצור קשר)."
        },
        "047": {
            "en": "Secret code must be entered where input file contains J1 "
                  "or J2 or J3 (contact prohibited).",
            "he": "חייב להזין קוד"
                  " סודי בקובץ קלט המכיל J1 או J2 או J3 (אסור ליצור קשר)."
        },
        "051": {
            "en": "Vehicle number defective.",
            "he": "מספר רכב שגוי."
        },
        "052": {
            "en": "Distance meter not entered.",
            "he": "מד מרחק לא הוזן."
        },
        "053": {
            "en": "Terminal not defined as gas station (petrol card passed or "
                  "incorrect transaction code).",
            "he": "מסוף לא מוגדר כתחנת דלק (הועבר כרטיס דלק או קוד עסקה שגוי)."
        },
        "057": {
            "en": "Identity Number Not Entered.",
            "he": "מספר תעודת זהות לא הוזנה."
        },
        "058": {
            "en": "CVV2 Not Entered.",
            "he": "CVV2 לא הוזן."
        },
        "059": {
            "en": "Identity Number and CVV2 Not Entered.",
            "he": "מספר תעודת זהות ו-CVV2 לא הוזנו."
        },
        "060": {
            "en": "Device not approved for user.",
            "he": "המכשיר לא מאושר למשתמש."
        },
        "061": {
            "en": "Device not authorized.",
            "he": "המכשיר לא מורשה."
        },
        "062": {
            "en": "Device is not activated.",
            "he": "המכשיר לא הופעל."
        },
        "063": {
            "en": "Device was deactivated.",
            "he": "המכשיר בוטל."
        },
        "064": {
            "en": "Device is not responding.",
            "he": "המכשיר לא מגיב."
        },
        "065": {
            "en": "Device Error.",
            "he": "שגיאת מכשיר."
        },
        "066": {
            "en": "Unrecognized Error.",
            "he": "שגיאה לא מזוהה."
        },
        "067": {
            "en": "Device maintenance.",
            "he": "תחזוקת מכשירים."
        },
        "068": {
            "en": "Low battery.",
            "he": "סוללה חלשה."
        },
        "069": {
            "en": "Transaction cancelled by user.",
            "he": "העסקה בוטלה על ידי המשתמש."
        },
        "070": {
            "en": "Unknown error.",
            "he": "שגיאה לא ידועה."
        },
        "071": {
            "en": "Device not activated for this operation.",
            "he": "המכשיר לא הופעל לפעולה זו."
        },
        "072": {
            "en": "Duplicate transaction.",
            "he": "עסקה כפולה."
        },
        "073": {
            "en": "Transaction already processed.",
            "he": "העסקה כבר עובדה."
        },
        "074": {
            "en": "Security Code Invalid.",
            "he": "קוד אבטחה לא תקין."
        },
        "075": {
            "en": "Security Code Missing.",
            "he": "קוד אבטחה חסר."
        },
        "076": {
            "en": "Transaction already completed.",
            "he": "העסקה כבר הושלמה."
        },
        "077": {
            "en": "Incorrect Card Type.",
            "he": "סוג כרטיס לא תקין."
        },
        "078": {
            "en": "Transaction amount is out of bounds.",
            "he": "סכום העסקה מחוץ לגבולות."
        },
        "079": {
            "en": "Payment method not supported.",
            "he": "שיטת תשלום לא נתמכת."
        },
        "080": {
            "en": "Time out.",
            "he": "זמן פג."
        },
        "081": {
            "en": "Too many attempts.",
            "he": "יותר מדי ניסיונות."
        },
        "082": {
            "en": "Transaction pending.",
            "he": "העסקה ממתינה."
        },
        "083": {
            "en": "Transaction delayed.",
            "he": "העסקה נדחתה."
        },
        "084": {
            "en": "Refund not possible.",
            "he": "זיכוי לא אפשרי."
        },
        "085": {
            "en": "Partial refund not possible.",
            "he": "זיכוי חלקי לא אפשרי."
        },
        "086": {
            "en": "Duplicate transaction - refund request.",
            "he": "עסקה כפולה - בקשת זיכוי."
        },
        "087": {
            "en": "Transaction cannot be refunded.",
            "he": "העסקה לא יכולה להתבטל."
        },
        "088": {
            "en": "Transaction cannot be disputed.",
            "he": "העסקה לא יכולה להיות במחלוקת."
        },
        "089": {
            "en": "Transaction disputed.",
            "he": "העסקה במחלוקת."
        },
        "090": {
            "en": "Transaction denied.",
            "he": "העסקה נדחתה."
        },
        "091": {
            "en": "Payment method not valid.",
            "he": "שיטת תשלום לא תקפה."
        },
        "092": {
            "en": "Payment not completed due to technical error.",
            "he": "התשלום לא הושלם עקב שגיאה טכנית."
        },
        "093": {
            "en": "Transaction reference not found.",
            "he": "לא נמצא אסמכתא לעסקה."
        },
        "094": {
            "en": "Merchant not authorized.",
            "he": "סוחר לא מורשה."
        },
        "095": {
            "en": "Merchant not valid.",
            "he": "סוחר לא תקף."
        },
        "096": {
            "en": "Payment failed due to insufficient funds.",
            "he": "התשלום נכשל עקב חוסר כספים."
        },
        "097": {
            "en": "Payment failed due to card issues.",
            "he": "התשלום נכשל עקב בעיות בכרטיס."
        },
        "098": {
            "en": "Transaction invalid.",
            "he": "העסקה לא תקפה."
        },
        "099": {
            "en": "Transaction approved, but with warning.",
            "he": "העסקה אושרה, אך עם אזהרה."
        },
        "100": {
            "en": "Invalid input data.",
            "he": "נתוני קלט לא תקינים."
        },
        "101": {
            "en": "Unknown error code.",
            "he": "קוד שגיאה לא ידוע."
        },
        "102": {
            "en": "Invalid authentication.",
            "he": "אימות לא תקין."
        },
        "103": {
            "en": "User not found.",
            "he": "משתמש לא נמצא."
        },
        "104": {
            "en": "User not authorized.",
            "he": "משתמש לא מורשה."
        },
        "105": {
            "en": "Account suspended.",
            "he": "החשבון הושעה."
        },
        "106": {
            "en": "Account closed.",
            "he": "החשבון סגור."
        },
        "107": {
            "en": "Account inactive.",
            "he": "החשבון אינו פעיל."
        },
        "108": {
            "en": "Transaction already exists.",
            "he": "העסקה כבר קיימת."
        },
        "109": {
            "en": "Account not found.",
            "he": "החשבון לא נמצא."
        },
        "110": {
            "en": "Invalid transaction code.",
            "he": "קוד עסקה לא תקין."
        },
        "111": {
            "en": "Transaction declined.",
            "he": "העסקה נדחתה."
        },
        "112": {
            "en": "Transaction already processed.",
            "he": "העסקה כבר עיבדה."
        },
        "113": {
            "en": "Transaction requires additional information.",
            "he": "העסקה דורשת מידע נוסף."
        },
        "114": {
            "en": "Invalid amount.",
            "he": "סכום לא תקין."
        },
        "115": {
            "en": "Payment not completed due to service unavailable.",
            "he": "התשלום לא הושלם עקב שירות לא זמין."
        },
        "116": {
            "en": "Transaction type not supported.",
            "he": "סוג העסקה לא נתמך."
        },
        "117": {
            "en": "Invalid card number.",
            "he": "מספר כרטיס לא תקין."
        },
        "118": {
            "en": "Card expired.",
            "he": "הכרטיס פג תוקף."
        },
        "119": {
            "en": "Transaction exceeds daily limit.",
            "he": "העסקה חורגת מהמגבלה היומית."
        },
        "120": {
            "en": "Transaction exceeds monthly limit.",
            "he": "העסקה חורגת מהמגבלה החודשית."
        },
        "121": {
            "en": "Transaction exceeds transaction limit.",
            "he": "העסקה חורגת מהמגבלה לעסקאות."
        },
        "122": {
            "en": "Fraud detected.",
            "he": "הונאה זוהתה."
        },
        "123": {
            "en": "Transaction cannot be completed due to restrictions.",
            "he": "לא ניתן להשלים את העסקה עקב מגבלות."
        },
        "124": {
            "en": "Security risk detected.",
            "he": "זוהה סיכון אבטחה."
        },
        "125": {
            "en": "Unexpected error occurred.",
            "he": "שגיאה לא צפויה אירעה."
        },
        "126": {
            "en": "Service temporarily unavailable.",
            "he": "שירות לא זמין באופן זמני."
        },
        "127": {
            "en": "Payment method temporarily unavailable.",
            "he": "שיטת תשלום לא זמינה באופן זמני."
        },
        "128": {
            "en": "Transaction could not be completed due to technical "
                  "difficulties.",
            "he": "לא ניתן להשלים את העסקה עקב קשיים טכניים."
        },
        "129": {
            "en": "Transaction requires manual review.",
            "he": "העסקה דורשת בדיקה ידנית."
        },
        "130": {
            "en": "Merchant account not found.",
            "he": "חשבון הסוחר לא נמצא."
        },
        "131": {
            "en": "Account verification failed.",
            "he": "אימות החשבון נכשל."
        },
        "132": {
            "en": "Account validation failed.",
            "he": "אימות חשבון נכשל."
        },
        "133": {
            "en": "Transaction abandoned.",
            "he": "העסקה ננטשה."
        },
        "134": {
            "en": "Transaction denied due to risk analysis.",
            "he": "העסקה נדחתה עקב ניתוח סיכונים."
        },
        "135": {
            "en": "Invalid account details.",
            "he": "פרטי חשבון לא תקינים."
        },
        "136": {
            "en": "Transaction requires user confirmation.",
            "he": "העסקה דורשת אישור משתמש."
        },
        "137": {
            "en": "Transaction cannot be processed at this time.",
            "he": "לא ניתן לעבד את העסקה בשלב זה."
        },
        "138": {
            "en": "Transaction may be subject to review.",
            "he": "העסקה עשויה להיות נתונה לבדיקה."
        },
        "139": {
            "en": "Transaction not completed.",
            "he": "העסקה לא הושלמה."
        },
        "140": {
            "en": "Payment limit reached.",
            "he": "הגיע לתקרת התשלום."
        },
        "141": {
            "en": "Insufficient information for processing.",
            "he": "מידע לא מספיק לעיבוד."
        },
        "142": {
            "en": "Service not available for this account.",
            "he": "שירות לא זמין עבור חשבון זה."
        },
        "143": {
            "en": "Transaction cannot be processed for this merchant.",
            "he": "לא ניתן לעבד את העסקה עבור סוחר זה."
        },
        "144": {
            "en": "Payment method restricted.",
            "he": "שיטת תשלום מוגבלת."
        },
        "145": {
            "en": "Transaction in progress.",
            "he": "העסקה בתהליך."
        },
        "146": {
            "en": "Data mismatch.",
            "he": "אי התאמה בנתונים."
        },
        "147": {
            "en": "Payment request cancelled.",
            "he": "בקשת התשלום בוטלה."
        },
        "148": {
            "en": "Merchant not registered.",
            "he": "הסוחר לא רשום."
        },
        "149": {
            "en": "Transaction cannot be processed due to incomplete "
                  "information.",
            "he": "לא ניתן לעבד את העסקה עקב מידע חסר."
        },
    }

    def _process_notification_data(self, notification_data):
        """ Override of payment to process the transaction based on Tranzila data.

        Note: self.ensure_one()

        :param dict notification_data: The feedback data sent by the provider
        :return: None
        """
        super()._process_notification_data(notification_data)
        if self.provider_code != 'tranzila':
            return
        if 'response' in notification_data:
            data_vals = notification_data.get('response')
            data_vals = json.loads(data_vals)
            status = data_vals.get('Response')
            self.provider_reference = data_vals.get('index')
        else:
            status = notification_data.get('Response')
            self.provider_reference = notification_data.get('index')
        if status == '000':
            existing_token = self.env['payment.token'].search([
                ('provider_id', '=', self.provider_id.id),
                ('partner_id', '=', self.partner_id.id),
                ('provider_ref', '=', notification_data.get('TranzilaTK'))])
            if self.tokenize and notification_data.get(
                    'TranzilaTK') and not existing_token:
                self._tranzila_tokenize_from_feedback_data(notification_data)
            self._set_done()
        else:
            error_message = self.ERROR_MESSAGES.get(status)
            if error_message:
                failure = error_message['he']
            else:
                failure = status  # Default to status if no message found

            # See https://github.com/kimtendu/woo-tranzila-gateway/blob/master/include/tranzila-gateway-woo-class.php
            # function tgwc_getTextForResponseCode( $code )
            self._set_error(
                "Tranzila: " + _("טרנזילה: התשלום נתקל בשגיאה, %s",
                                 failure)
            )

    def _tranzila_tokenize_from_feedback_data(self, notification_data):

        """ Create a new token based on the feedback data.

        Note: self.ensure_one()

        :param dict notification_data: The feedback data sent by the provider
        :return: None_logger
        """
        self.ensure_one()
        token_data = {
            'provider_id': self.provider_id.id,
            'payment_details': payment_utils.singularize_reference_prefix(prefix=notification_data.get('TranzilaTK')[-4:]) ,
            'partner_id': self.partner_id.id,
            'payment_method_id': self.env.ref("payment.payment_method_card").id,
            'provider_ref': notification_data.get('TranzilaTK'),
            'ccno': notification_data.get('TranzilaTK')[-4:],
            'expyear': notification_data.get('expyear'),
            'expmonth': notification_data.get('expmonth'),
            # 'verified': True,  # The payment is authorized, so the payment method is valid
        }
        token = self.env['payment.token'].create(token_data)
        self.write({
            'token_id': token.id,
            'tokenize': False,
        })
        _logger.info(
            "created token with id %s for partner with id %s", token.id, self.partner_id.id
        )