# -*- coding: utf-8 -*-

from odoo import models
from collections import defaultdict


class LandingCostReportXlsx(models.AbstractModel):
    _name = 'report.bizzup_landing_cost_report.report_landing_cost'
    _inherit = 'report.report_xlsx.abstract'

    def calculate_services(self, product_id):
        return self.env["stock.valuation.adjustment.lines"].search(
            [('product_id', '=', product_id[0])]
        )

    def review_header(self, records):
        # Filter records that have linked landed costs
        landed_costs = records.filtered(lambda inv: inv.landed_costs_ids)

        # Collect all related landed cost names
        cost_names = []
        for rec in landed_costs:
            for landed_cost in rec.landed_costs_ids:
                cost_names.append(landed_cost.name)

        # Now search for related valuation lines using cost name
        valuation_data = self.env["stock.landed.cost"].search([
            ('name', '=', cost_names)
        ])

        return valuation_data

    def calculate_services_header(self, records):
        # Filter records that have linked landed costs
        landed_costs = records.filtered(lambda inv: inv.landed_costs_ids)

        # Collect all related landed cost names
        cost_names = []
        for rec in landed_costs:
            for landed_cost in rec.landed_costs_ids:
                cost_names.append(landed_cost.name)

        # Now search for related valuation lines using cost name
        valuation_data = self.env["stock.landed.cost"].search([
            ('name', '=', cost_names)
        ])
        return valuation_data. valuation_adjustment_lines

    def total_loaded_cost_local(self, product_id, records):
        domain = [
            ("move_id", "in", records.ids),
            ('product_id', '=', product_id[0])
        ]
        price_total = sum(self.env["account.move.line"].search(domain).filtered(
            lambda l: l.is_landed_costs_line
        ).mapped("price_subtotal"))
        return price_total

    def find_product_currency(self, product_id):
        return self.env["product.product"].browse(product_id[0]).currency_id.symbol

    def generate_xlsx_report(self, workbook, data, records):
        report_name = "Landing Cost Report"
        sheet = workbook.add_worksheet(report_name)
        bold = workbook.add_format({'bold': True})

        # Get landed cost services
        length_lines = self.review_header(records)
        unique_services = [f"{rec.product_id.name}" for rec in length_lines.cost_lines]
        list_of_service = list(dict.fromkeys(unique_services))

        headers = [
                      'Product Name', 'Quantity', 'Unit Price', 'Total FOB', "Currency",
                      'Total FOB (Local)'
                  ] + list_of_service + [
                      'Total Loaded Cost (Local)', 'Total Cost before VAT',
                      'Total Cost incl. VAT', 'Unit Cost excl. VAT',
                      'Unit Cost incl. VAT', 'Multiplier'
                  ]

        for col, head in enumerate(headers):
            sheet.write(1, col, head, bold)

        account_move_line_obj = self.env["account.move.line"]
        domain = [
            ("move_id", "in", records.ids),
            ('is_landed_costs_line', '=', False)
        ]
        group_by_product = account_move_line_obj.read_group(
            domain=domain,
            fields=["product_id", "quantity:sum", "price_unit", "price_subtotal:sum","tax_ids"],
            groupby=["product_id"]
        )

        row = 2
        total_columns = defaultdict(float)
        service_names = list_of_service

        for line in group_by_product:
            if not line["product_id"]:
                continue

            product_id = line["product_id"][0]
            product_name = line["product_id"][1]
            quantity = line["quantity"]
            fob = line["price_subtotal"]
            currency = self.find_product_currency(line["product_id"])

            # Get all matching lines for average price calculation
            all_lines = account_move_line_obj.search([
                ("move_id", "in", records.ids),
                ("product_id", "=", product_id),
                ('is_landed_costs_line', '=', False)
            ])
            unit_price = sum(all_lines.mapped("price_unit"))

            # Get valuation lines related to this product
            services = self.calculate_services_header(records)
            product_services = [s for s in services if s.product_id.id == product_id]

            service_totals = defaultdict(float)
            for serv in product_services:
                service_name = serv.cost_line_id.product_id.name
                service_totals[service_name] += serv.additional_landed_cost

            total_loaded_cost = sum(service_totals.values())
            total_cost_before_vat = fob + total_loaded_cost
            total_cost_incl_vat = total_cost_before_vat * 1.18

            unit_ex = total_cost_before_vat / quantity if quantity else 0
            unit_in = total_cost_incl_vat / quantity if quantity else 0
            multiplier = total_cost_before_vat / fob if fob else 0

            sheet.write(row, 0, product_name)
            sheet.write(row, 1, quantity)
            sheet.write(row, 2, unit_price)
            sheet.write(row, 3, fob)
            sheet.write(row, 4, currency)
            sheet.write(row, 5, fob)  # Local = base price

            total_columns[1] += quantity
            total_columns[2] += unit_price  # will average later
            total_columns[3] += fob
            total_columns[5] += fob

            col = 6
            for service_name in service_names:
                val = service_totals.get(service_name, 0)
                sheet.write(row, col, val)
                total_columns[col] += val
                col += 1

            sheet.write(row, col, total_loaded_cost)
            total_columns[col] += total_loaded_cost
            col += 1

            sheet.write(row, col, total_cost_before_vat)
            total_columns[col] += total_cost_before_vat
            col += 1

            sheet.write(row, col, total_cost_incl_vat)
            total_columns[col] += total_cost_incl_vat
            col += 1

            sheet.write(row, col, unit_ex)
            total_columns[col] += unit_ex
            col += 1

            sheet.write(row, col, unit_in)
            total_columns[col] += unit_in
            col += 1

            sheet.write(row, col, multiplier)
            total_columns[col] += multiplier
            col += 1

            row += 1

        # ---- Add "Total" Row ----
        sheet.write(row, 0, "TOTAL", bold)
        for col in range(1, len(headers)):
            if col == 4:
                continue  # Skip 'Currency' column
            value = total_columns[col]
            sheet.write(row, col, value, bold)
