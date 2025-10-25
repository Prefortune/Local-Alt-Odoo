from odoo import models , fields
import logging
_logger = logging.getLogger(__name__)

class AccountMove(models.Model):
    _inherit = 'account.move'

    is_reconcile_processed = fields.Boolean(default=False)

    def action_reconcile_all_unpaid(self):
        
        # this code for which is not match in first round

        # journal = self.env['account.journal'].search([('type', '=', 'bank')], limit=1)
        # all_trans = self.env['account.bank.statement.line'].search([
        #     ('is_reconciled', '=' , False),
        #     ('journal_id', '=', journal.id),
        # ])
        # _logger.info("--------- account.bank.statement.line ----------- %s",len(all_trans))
        # counter = 0
        # for trans in all_trans:
        #     _logger.info("account.bank.statement.line amount ---------------- %s",trans.amount)
        #     payment = self.env['account.payment'].search([('amount','=',abs(trans.amount))],limit=1)
        #     if payment:
        #         trans.payment_ref = payment.name
        #         counter +=1
        # _logger.info("------------ payment matching ------------ %s",counter)


        # this is for invoice code 

        journal = self.env['account.journal'].search([('type', '=', 'bank')], limit=1)
        if not journal:
            _logger.warning("No bank journal found!")
            return
        _logger.info("journal ---------- %s",journal)

        invoices = self.env['account.move'].search([
            ('move_type', '=', 'out_invoice'),
            ('state', '=', 'posted'),                
            ('payment_state', '=', 'in_payment'),      
            ('is_reconcile_processed', '=', False),
            ('payment_reference', '!=', False),         
        ])
        _logger.info("total invoices to reconcile: %s", len(invoices))
        count = 0
        for inv in invoices:
            payment = self.env['account.payment'].search([('ref','=',inv.name)],limit=1)
            if payment:
                # _logger.info("INV ID %s",inv)
                count += 1
                invoice_data = {
                    'date' : inv.invoice_date,
                    'amount' : inv.amount_total,
                    'payment_ref' : inv.name,
                    'partner_id': payment.partner_id.id,
                    'journal_id' : journal.id
                }
                self.env['account.bank.statement.line'].create(invoice_data)
                inv.is_reconcile_processed = True
                self.env.cr.commit() 
                _logger.info("invoice_data WITH count %s, %s %s",count , invoice_data, inv.id)
            else:
                count += 1
                _logger.info("payment not found %s %s %s",count,inv.name,inv.id)


        # this is for bill code

        # journal = self.env['account.journal'].search([('type', '=', 'bank')], limit=1)
        # if not journal:
        #     _logger.warning("No bank journal found!")
        #     return
        # _logger.info("journal ---------- %s",journal)
        # invoices = self.env['account.move'].search([
        #     ('move_type', '=', 'in_invoice'),
        #     ('state', '=', 'posted'),                
        #     ('payment_state', '=', 'in_payment'),      
        #     ('is_reconcile_processed', '=', False),
        # ])
        # _logger.info("total invoices to reconcile: %s", len(invoices))
        # count = 0
        # for inv in invoices:
        #     count += 1
        #     if inv.currency_id != inv.company_currency_id:
        #         if inv.name == '/':
        #             paymetn_data = self.env['account.payment'].search([
        #                 ('amount','=',inv.amount_total),
        #                 ('date','=',inv.invoice_date)
        #             ],limit=1)
        #             if paymetn_data:
        #                 invoice_data = {
        #                     'date' : paymetn_data.date,
        #                     'foreign_currency_id' : inv.currency_id.id,
        #                     'amount_currency' : inv.amount_total,
        #                     'payment_ref' : paymetn_data.ref,
        #                     'partner_id': paymetn_data.partner_id.id,
        #                     'journal_id' : journal.id
        #                 }
        #             else:
        #                 invoice_data = {
        #                     'date' : inv.invoice_date,
        #                     'foreign_currency_id' : inv.currency_id.id,
        #                     'amount_currency' : inv.amount_total,
        #                     'payment_ref' : inv.name,
        #                     'partner_id': inv.partner_id.parent_id.id if inv.partner_id.parent_id else inv.partner_id.id,
        #                     'journal_id' : journal.id
        #                 }
        #         else:
        #             invoice_data = {
        #                     'date' : inv.invoice_date,
        #                     'foreign_currency_id' : inv.currency_id.id,
        #                     'amount_currency' : inv.amount_total,
        #                     'payment_ref' : inv.name,
        #                     'partner_id': inv.partner_id.parent_id.id if inv.partner_id.parent_id else inv.partner_id.id,
        #                     'journal_id' : journal.id
        #             }
        #     else:
        #         if inv.name == '/':
        #             paymetn_data = self.env['account.payment'].search([
        #                 ('amount','=',inv.amount_total),
        #                 ('date','=',inv.invoice_date)
        #             ],limit=1)
        #             if paymetn_data:
        #                 invoice_data = {
        #                     'date' : paymetn_data.date,
        #                     'amount' : -inv.amount_total,
        #                     'payment_ref' : paymetn_data.ref,
        #                     'partner_id': paymetn_data.partner_id.id,
        #                     'journal_id' : journal.id
        #                 }
        #             else:
        #                 invoice_data = {
        #                     'date' : inv.invoice_date,
        #                     'amount' : -inv.amount_total,
        #                     'payment_ref' : inv.name,
        #                     'partner_id': inv.partner_id.parent_id.id if inv.partner_id.parent_id else inv.partner_id.id,
        #                     'journal_id' : journal.id
        #                 }
        #         else:
        #             invoice_data = {
        #                     'date' : inv.invoice_date,
        #                     'amount' : -inv.amount_total,
        #                     'payment_ref' : inv.name,
        #                     'partner_id': inv.partner_id.parent_id.id if inv.partner_id.parent_id else inv.partner_id.id,
        #                     'journal_id' : journal.id
        #             }
        #     self.env['account.bank.statement.line'].create(invoice_data)
        #     inv.is_reconcile_processed = True
        #     self.env.cr.commit() 
        #     _logger.info("invoice_data WITH count %s, %s %s",count , invoice_data, inv.id)

        

class ReconcileWizardForm(models.TransientModel):
    _name = 'reconcile.wizard.form'
    _description = 'Manual Reconciliation Wizard'

    def action_run_reconciliation(self):
        self.env['account.move'].action_reconcile_all_unpaid()
        return {'type': 'ir.actions.act_window_close'}