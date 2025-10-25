# -*- coding: utf-8 -*-
# Copyright (C) Gilliam Management Services and Information Systems, Ltd. (the owner of Bizzup), 2021, 2022, 2023, 2024, 2025
# All Rights Reserved to Gilliam Management Services and Information Systems, Ltd.
# Unauthorized copying, editing or printing of this file, in any way is strictly prohibited
# Proprietary and confidential for more information, please contact
# lg@bizzup.app

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class ProjectTask(models.Model):
    _inherit = 'project.task'

    import_case_type = fields.Selection([
        ('import_case', 'Import Case'),
        ('other', 'Other'),
    ], compute="_compute_import_case_type", store=True, string='Type',)
    import_case_compute = fields.Boolean('Check Project Group', compute="_compute_project_group")

    import_case_seq = fields.Char(string='Import Case ID', readonly=True, copy=False)
    invoice_date = fields.Date(string="Invoice Date")
    booking = fields.Char(string="Booking")
    send_date = fields.Date(string="Send Date")
    expected_date = fields.Date(string="Expected Date")
    amount_total = fields.Float(string="Amount Total")

    scheduled_date = fields.Date(string="Scheduled Date")
    release_date = fields.Date(string="Release Date")
    date_done = fields.Date(string="Date Dome")
    date = fields.Date(string="Date")
    picking_id = fields.Many2one('stock.picking', "Picking")
    port_of_departure_ids = fields.One2many('port.of.departure', 'task_id', string="Port of Departure",)
    port_of_arrival_ids = fields.One2many('port.of.arrival', 'task_id', string="Port of Arrival",)
    seger_number = fields.Char(string="Seger Number")
    size = fields.Char(string="Size")

    number_of_containers = fields.Integer(string="Number of Containers", compute="_compute_number_of_containers")
    related_number_of_containers = fields.Integer(string="Number of Containers",)
    general_notes = fields.Text(string="General Notes")
    total_amount = fields.Float(string="Total Amount", compute="_compute_total_amount")
    related_total_amount = fields.Float(string="Total Amount")
    related_transfer_ids = fields.One2many(
        'stock.picking',
        'import_case_id',
        string='Related Transfers',
        domain=[('picking_type_code', '=', 'incoming')],
        readonly=True
    )
    manual_move_ids = fields.One2many(
        'related.transfer', 'task_id',
        string='Manually Linked Transfers'
    )
    related_picking_ids = fields.One2many(
        'related.picking', 'task_id',
        string='Manually Linked Transfers'
    )

    bill_ids = fields.One2many(
        'related.move', 'task_id',
        string='Manually Linked Bills'
    )

    all_transfer_ids = fields.One2many(
        'stock.move',
        compute='_compute_all_transfer_ids',
        string='Transfers',
        store=False
    )
    related_containers = fields.Integer(string="Number of Containers")

    manual_transfer_ids = fields.One2many(
        'stock.picking',
        'import_case_id',
        store=True,
        string='Manually Added Transfers'
    )
    related_container_ids = fields.One2many('stock.picking.batch', 'task_id', string="Related Containers")
    manual_container_ids = fields.One2many('related.stock.picking.batch', 'task_id', string="Related Containers", store=True)
    store_manual_container_ids = fields.Many2many('stock.picking.batch', 'task_id', string="Related Containers",
                                                 compute="_store_manual_container_ids" )
    container_ids = fields.Many2many('stock.picking.batch', 'task_id', string="Related Containers")

    related_purchase_order_ids = fields.Many2many(
        'purchase.order',
        string="Related Purchase Orders",
        compute="_compute_related_purchase_orders",
    )
    new_related_purchase_order_ids = fields.Many2many(
        'purchase.order',
        string="Related Purchase Orders",
    )
    related_bill_ids = fields.One2many(
        'account.move', 'import_case_id',
        string='Related Bills',
        domain=[('move_type', 'in', ['in_invoice', 'in_refund'])]
    )
    picking_ids = fields.Many2many('stock.picking', string="All Picking",
                                   compute='_compute_picking_ids')
    store_picking_ids = fields.Many2many('stock.picking', string="All Transfer",)

    assigned_picking_ids = fields.Many2many(
        'stock.picking',
        'task_assigned_picking_rel',  # relation table
        'task_id',
        'picking_id',
        string='Assigned Pickings (technical)',
        help='Pickings that were ever assigned automatically to this task.'
    )

    def _store_manual_container_ids(self):
        """
        Updates store_manual_container_ids and container_ids with batch IDs
        from the selected manual_container_ids.
        """
        self.store_manual_container_ids = self.manual_container_ids.mapped('batch_id')
        self.container_ids = self.manual_container_ids.mapped('batch_id')

    @api.depends('related_transfer_ids.move_ids', 'manual_move_ids.picking_id.move_ids')
    def _compute_all_transfer_ids(self):
        """
        Computes and assigns all stock moves from both related transfers and manual pickings to the task.
        Also handles import_case_id assignment carefully:
        only set if picking wasn't manually removed after first assignment.
        """
        for task in self:
            # Moves from related_transfer_ids
            from_related = task.related_transfer_ids.mapped('move_ids')

            # Moves from manual_move_ids' pickings
            manual_moves = self.env['stock.move']
            for line in task.manual_move_ids:
                picking = line.picking_id
                if picking:
                    manual_moves |= picking.move_ids

                    # if picking was never assigned before, assign and remember
                    if picking not in task.assigned_picking_ids:
                        if not picking.import_case_id:
                            picking.import_case_id = task.id
                            task.assigned_picking_ids = [(4, picking.id)]  # add to memory

            # Combine moves
            task.all_transfer_ids = from_related | manual_moves

    def _compute_related_purchase_orders(self):
        """
        Computes and assigns related purchase orders from the task's related transfers.
        """
        for task in self:
            pos = self.env['purchase.order']
            for picking in task.related_transfer_ids:
                if picking.purchase_id:
                    pos |= picking.purchase_id
            task.related_purchase_order_ids = pos
            task.new_related_purchase_order_ids = pos

    @api.depends('project_id')
    def _compute_import_case_type(self):
        """
        Sets import_case_type based on the related project's project_type if not already set.
        """
        for rec in self:
            if not rec.import_case_type:
                rec.import_case_type = rec.project_id.project_type

    @api.model
    def create(self, vals):
        """
        Overrides create to assign a sequence to import_case_seq and set import_case_type
        if the type is 'import_case'.
       """
        res = super().create(vals)
        if res.import_case_type == 'import_case':
            res.import_case_seq = self.env['ir.sequence'].next_by_code('project.task.import.case')
            res.import_case_type = res.project_id.project_type
        return res

    def _compute_picking_ids(self):
        """
           Computes and updates related stock and accounting records for a task.

           - Sets picking_ids and store_picking_ids based on manual_move_ids.
           - For each related container name, links the corresponding picking batch if not already linked.
           - For each related transfer name, links the corresponding stock picking if not already linked.
           - For each related bill name, links the corresponding vendor bill (account.move) if not already linked.

           Ensures that relationships are created only when not already present to avoid duplication.
        """
        for task in self:
            if task.related_container_ids:
                existing_batches = task.manual_container_ids.mapped('batch_id')
                batch_names = task.related_container_ids.mapped('name')
                for name in batch_names:
                    batch = self.env['stock.picking.batch'].search([('name', '=', name)], limit=1)
                    if batch and batch not in existing_batches:
                        task.manual_container_ids = [(4, batch.id, 0)] + [(0, 0, {'batch_id': batch.id})]

            if task.related_transfer_ids:
                transfer_names = task.related_transfer_ids.mapped('name')
                existing_picking_ids = task.related_picking_ids.mapped('picking_id.id')

                for name in transfer_names:
                    transfer = self.env['stock.picking'].search([('name', '=', name)], limit=1)
                    if transfer and transfer.id not in existing_picking_ids:
                        task.related_picking_ids = [(0, 0, {'picking_id': transfer.id})]

                # Unlink unrelated pickings (very important)
                to_unlink = task.related_picking_ids.filtered(
                    lambda line: line.picking_id.name not in transfer_names
                )
                if to_unlink:
                    to_unlink.unlink()

            if task.related_bill_ids:
                bill_names = task.related_bill_ids.mapped('name')
                existing_bill_ids = task.bill_ids.mapped('bill_id.id')
                for name in bill_names:
                    bill = self.env['account.move'].search([('name', '=', name)], limit=1)
                    if bill and bill.id not in existing_bill_ids:
                        task.bill_ids = [(0, 0, {'bill_id': bill.id,})]

            picking = task.manual_move_ids.mapped('picking_id')
            task.picking_ids = picking
            task.store_picking_ids = picking

    @api.depends('related_container_ids')
    def _compute_number_of_containers(self):
        """
        Computes the number of containers linked to the task.
        Updates both number_of_containers and related_number_of_containers fields.
        """
        for record in self:
            record.number_of_containers = len(record.manual_container_ids)
            record.related_number_of_containers = len(record.manual_container_ids)

    @api.depends('related_bill_ids')
    def _compute_total_amount(self):
        """
        Computes the total and related total amount from linked bills.
        """
        for record in self:
            record.total_amount = sum(record.related_bill_ids.mapped('amount_total_signed'))
            record.related_total_amount = sum(record.related_bill_ids.mapped('amount_total_signed'))

    def _compute_project_group(self):
        """
        Sets a flag based on whether the current user is a project manager.
        """
        for rec in self:
            if not self.env.user.has_group('project.group_project_manager'):
                rec.import_case_compute = True
            else:
                rec.import_case_compute = False

    @api.onchange('expected_date')
    def _onchange_expected_date(self):
        """
        Validates that expected_date is not earlier than send_date.
        Updates scheduled_date on related pickings if not done or cancelled.
        """
        if self.send_date and self.expected_date and self.expected_date < self.send_date:
            if self.env.lang == 'en_US':
                raise ValidationError("Expected date cannot be earlier than Send date.")
            else:
                raise ValidationError("תאריך הגעה צפוי לא יכול להיות מוקדם מתאריך השליחה")

        for transfer in self.related_picking_ids.filtered(lambda record: record.state not in ('done', 'cancel')):
            if transfer.picking_id:
                transfer.picking_id.write({'scheduled_date': self.expected_date})
                transfer.update({'scheduled_date': transfer.picking_id.scheduled_date})

    @api.onchange('send_date')
    def _onchange_send_date(self):
        """
        Validates that send_date is not later than expected_date.
        """
        if self.expected_date and self.send_date > self.expected_date:
            if self.env.lang == 'en_US':
                raise ValidationError("Send date cannot be later than Expected date.")
            else:
                raise ValidationError("תאריך שליחה לא יכולה להיות מאוחר יותר מתאריך צפוי")
