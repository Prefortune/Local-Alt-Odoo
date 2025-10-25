Bizzup Journal Entry for Masav
=======================

This module enhances the vendor payment process in Odoo by introducing custom logic for managing journal entries related to Masav processing.


Features
=============

* ✅ Adds a new boolean field Masav Entry on vendor payments.

  * Default is False.
  * Automatically set to True once a Masav-related journal entry is created.
* ✅ Adds a new Account Tag named `צל` during module installation.

  * This tag must be manually assigned to relevant accounts in the Chart of Accounts.
* ✅ Adds a Server Action: Make Journal Entry

  * Visible only for payments where Masav Entry is False.
  * Generates journal entries for eligible vendor payments.
  * Redirects to the newly created journal entry form view after processing.
* ✅ Adds a new Boolean Setting in Accounting Settings:

  * Label: Entry for payments after Masav
  * If enabled, the system automatically runs the Make Journal Entry server action during Masav report printing.
* ✅ Journal Validation:

  * If a journal with code TMSV is not found, a UserError is raised.
* ✅ Smart Masav Report Handling:

  * While printing the Masav report:

    * All vendor payments where Masav Entry is False are processed to create journal entries.
    * If a payment fails to process (e.g., due to a missing journal), it is skipped instead of stopping the whole operation.
    * Report is still printed for successfully processed payments.
    * No redirection occurs to journal entries during this action.


Configuration
=============

1. Navigate to Accounting → Configuration → Chart of Accounts.

   * Assign the `צל` account tag (created during installation) to the relevant accounts manually.

2. Go to Accounting → Configuration → Settings.

   * Enable the Boolean: Entry for payments after Masav if you want Masav journal entries to be created during Masav report printing.

3. Use the "Make Journal Entry" server action from the vendor payment form when Masav Entry is False.

   * Ensure journal with code TMSV exists and is properly configured.

Company
-------
* `Gilliam Management Services and Information Systems, Ltd. <https://www.bizzup.app>`__

Contacts
--------
* Website: https://www.bizzup.app

Bug Tracker
-----------
Please feel free to contact us using the contact details you're asked for any issues or concerns related to this module.

Maintainer
==========
.. image:: https://www.bizzup.app/web/image/website/8/logo/Bizzup.app?unique=2751610
   :target: https://www.bizzup.app

Gilliam Management Services and Information Systems, Ltd. maintain this module.
