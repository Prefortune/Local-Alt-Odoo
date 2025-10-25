# -*- coding: utf-8 -*-

{
    "name": "Bizzup Contact Archive Search",
    "description": """
        Ticket : HT01263 | (Make changes in contact - Matzman)

Use cases:

1) In the default search
   a) In the default search in contact, users will be able to search for contact
     by mobile or by phone
   b) In the default search in contact, users will be able to search also unactive
     contacts.

2) Right now, when a user try to add to contact a VAT that is already existing
   in another contact, he get an message

   a) I want to create a message like this also if the mobile exists for another contact.
   
   Added option to search by vat or mobile/phone in the search view of contact
.""",
    "version": "18.0.2.0.0",
    "category": "Contacts",
    "license": "Other proprietary",
    "author": "Lilach Gillam",
    "website": "www.bizzup.app",
    "depends": [
        "contacts",'sms','sale_management','point_of_sale',
    ],
    "data": [
        "views/res_partner_form_view.xml",
    ],
    "assets": {
        "point_of_sale._assets_pos": [
            "bizzup_contact_archive_search/static/src/**/*",
        ],
    },
    "demo": [],
    "installable": True,
    "application": False,
}
