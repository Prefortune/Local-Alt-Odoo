# Bizzup Journal Entry for Masav

### Technical Name: bizzup_journal_entry_masav


### [18.0.1.0.0] - 2025-06-09 | HT01743
- Added new boolean field "Masav entry" to vendor payment (readonly is value is False)
- Created account tag with name 'צל' during module installation
- need to **assign this account tag 'צל' to the appropriate accounts in the Chart of Accounts**
- Add new server action "Make journal entry", to the payment view
- action only for which the payment has "Masav entry" boolean is false
- If journal with code 'TMSV' is not found, raises a UserError
- after the action process, we did mark as true for "Masav entry" boolean to the payment and redirect the view for newly created journal entries for masav
- added new boolean to accounting setting how called "Entry for payments after Masav"
- If the boolean is TRUE:- If a user print report to Masav the action will be excuted and then the boolean "Masav entry" will be TRUE
- Find all vendor payments that "Masav entry" boolean is false, we will execute server action "Make journal entry" when press the print report
- instead of raising a validation error when the "Print Masav Report", Masav journal entry logic is executed, we should skip that payment so the remaining payments can still be processed and print the report.
- we can not redirect the newly created journal entries for masav during print the report

### [18.0.1.0.1] - 2025-06-11 | HT01743
- Removed un-used file
- Updated the warning message

### [18.0.1.0.2] - 2025-06-11 | HT01743
- Hide 'Masav Entry' field on payment if the user have not group (Administration - Settings) assigned
- 'Masav Entry' field value not copied during duplicate record of payment