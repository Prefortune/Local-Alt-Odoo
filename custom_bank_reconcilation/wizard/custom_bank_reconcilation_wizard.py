from odoo import _, api, fields, models
from datetime import timedelta
from odoo.osv.expression import OR, AND

class CustomBankReconcilationWizard(models.TransientModel):
    _name = 'custom.bank.reconcilation.wizard'
    _description = 'Custom Bank Reconciliation Wizard'
    _rec_name = 'journal_id'

    custom_bank_reconcilation_line_ids = fields.One2many(
        'custom.bank.reconcilation.line',
        'wizard_id',
        string='Bank Reconciliation Lines',
    )
    account_ids = fields.Many2many(
        'account.account',
        string='Accounts',
        domain="[('deprecated', '=', False),('reconcile','=',True)]")
    date_tolerance = fields.Integer(string='Date Tolerance', default=4)
    journal_id = fields.Many2one(
        'account.journal',
        string='Journal',
        domain="[('type', 'in', ['bank','cash'])]",
        required=True,
    )
    match_by_ref = fields.Boolean(string='Match by Reference')
    match_by_amount = fields.Boolean(string='Match by Amount', default=True, readonly=True)
    match_by_tolerance = fields.Boolean(string='Match by Tolerance')

    @api.onchange('journal_id', 'match_by_ref', 'match_by_tolerance', 'date_tolerance', 'account_ids')
    def _onchange_filters(self):
        if not self.journal_id:
            return

        self.custom_bank_reconcilation_line_ids = [(5, 0, 0)]
        stmt_lines = self.env['account.bank.statement.line'].search([
            ('journal_id', '=', self.journal_id.id),
            ('is_reconciled', '=', False),
            ('amount', '!=', 0),
        ], order='id asc')

        already_matched_ids = set()
        new_lines = []

        for stmt_line in stmt_lines:
            move_line = self._find_matching_move_line(stmt_line, already_matched_ids)
            if move_line:
                already_matched_ids.add(move_line.id)

            new_lines.append((0, 0, {
                'bank_statement_line_id': stmt_line.id,
                'amount': stmt_line.amount,
                'company_id': stmt_line.company_id.id,
                'currency_id': stmt_line.currency_id.id,
                'move_line_id': move_line.id if move_line else False,
                'do_reconcile': bool(move_line),
            }))

        # Sort: lines with move_line_id come first
        new_lines.sort(key=lambda x: x[2].get('move_line_id') is False)

        self.custom_bank_reconcilation_line_ids = new_lines


    def _find_matching_move_line(self, stmt_line, already_matched_ids):
        domain = [
            ('parent_state', '=', 'posted'),
            ('account_id.reconcile', '=', True),
            ('reconciled', '=', False),
            ('company_id', '=', stmt_line.company_id.id),
            ('amount_residual', '=', stmt_line.amount),
            ('id', 'not in', list(already_matched_ids)),
        ]

        if self.account_ids:
            domain.append(('account_id', 'in', self.account_ids.ids))

        if stmt_line.partner_id:
            domain.append(('partner_id', '=', stmt_line.partner_id.id))

        if self.match_by_ref:
            ref_domain = self._get_reference_domain(stmt_line)
            if ref_domain:
                move_line = self.env['account.move.line'].search(AND([domain, ref_domain,]), limit=1)
                if move_line:
                    return move_line

        if self.match_by_tolerance:
            tolerance_days = self.date_tolerance
            date_start = stmt_line.date - timedelta(days=tolerance_days)
            date_end = stmt_line.date + timedelta(days=tolerance_days)
            date_domain = [('date', '>=', date_start), ('date', '<=', date_end)]
            move_line = self.env['account.move.line'].search(AND([domain, date_domain]), limit=1)
            if move_line:
                return move_line

        return self.env['account.move.line'].search(domain, limit=1)

    def _get_reference_domain(self, stmt_line):
        if not stmt_line.payment_ref:
            return []
        return OR([
            [('payment_id.memo', 'ilike', stmt_line.payment_ref)],
            [('name', 'ilike', stmt_line.payment_ref)],
            [('ref', 'ilike', stmt_line.payment_ref)],
            [('move_id.name', 'ilike', stmt_line.payment_ref)],
            [('move_id.ref', 'ilike', stmt_line.payment_ref)],
        ])

    def action_confirm(self):
        self.ensure_one()
        for line in self.custom_bank_reconcilation_line_ids.filtered(lambda l: l.do_reconcile and l.move_line_id):
            _liquidity_lines, suspense_lines, _other_lines = line.bank_statement_line_id._seek_for_lines()
            suspense_lines.write({'account_id': line.move_line_id.account_id.id})
            (suspense_lines | line.move_line_id).filtered(lambda l: not l.reconciled).reconcile()


class CustomBankReconcilationLine(models.TransientModel):
    _name = 'custom.bank.reconcilation.line'
    _description = 'Custom Bank Reconciliation Line'

    wizard_id = fields.Many2one('custom.bank.reconcilation.wizard', string='Wizard')
    bank_statement_line_id = fields.Many2one('account.bank.statement.line', string='Bank Statement Line')
    date = fields.Date(string='Date', related='bank_statement_line_id.date')
    move_line_id = fields.Many2one('account.move.line', string='Move Line')
    do_reconcile = fields.Boolean(string='Reconcile')
    move_id = fields.Many2one('account.move', string='Move', related='move_line_id.move_id')
    bank_statement_id = fields.Many2one('account.bank.statement', string='Bank Statement', related='bank_statement_line_id.statement_id')
    amount = fields.Monetary(string='Amount', related='bank_statement_line_id.amount')
    company_id = fields.Many2one('res.company', string='Company', related='bank_statement_line_id.company_id')
    currency_id = fields.Many2one('res.currency', string='Currency', related='bank_statement_line_id.currency_id')
