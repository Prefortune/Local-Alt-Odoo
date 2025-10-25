from odoo import models, fields, api
from odoo.exceptions import UserError
import base64
import logging
import tempfile
import binascii
import openpyxl
from collections import defaultdict
import os

_logger = logging.getLogger(__name__)

class ImportStockMoveWizard(models.TransientModel):
    _name = 'import.stock.move.wizard'
    _description = 'Import Quantities from Excel for Picking'

    file_name = fields.Char(string='File Name')
    move_file = fields.Binary(string='File', required=True)
    picking_id = fields.Many2one('stock.picking', string='Picking', required=True)

    def _validate_file(self, file_data):
        """Validate file size and type"""
        if not file_data:
            raise UserError('Please upload a file first.')
        
        # Check file size (max 10MB)
        file_size = len(binascii.a2b_base64(file_data))
        if file_size > 10 * 1024 * 1024:  # 10MB
            raise UserError('File size exceeds 10MB limit.')
        
        # Check file type
        if not self.file_name or not self.file_name.lower().endswith(('.xlsx', '.xls')):
            raise UserError('Please upload an Excel file (.xlsx or .xls)')

    def _get_column_indices(self, sheet):
        """Find required column indices in the Excel sheet"""
        header_row = [str(cell.value).strip() if cell.value is not None else '' for cell in next(sheet.iter_rows(min_row=1, max_row=1))]
        
        required_column_mappings = {
            'default_code': ['default_code', 'customer sku', 'SKU_STOCK'],
            'quantity': ['unit', 'quantity', 'qty', 'amount', 'units']
        }
        
        def clean_text(text):
            if not text:
                return ''
            text = ''.join(c.lower() for c in str(text) if c.isalnum() or c.isspace() or c == '/')
            return ' '.join(text.split())
        
        column_indices = {}
        for required_name, possible_names in required_column_mappings.items():
            found = False
            for possible_name in possible_names:
                clean_possible = clean_text(possible_name)
                for idx, header in enumerate(header_row):
                    clean_header = clean_text(header)
                    if clean_possible == clean_header or (clean_possible in clean_header and len(clean_possible) > 2) or (clean_header in clean_possible and len(clean_header) > 2):
                        column_indices[required_name] = idx
                        _logger.info(f"Found column '{required_name}' at index {idx}: '{header}'")
                        found = True
                        break
                if found:
                    break
            if not found:
                available_columns = ', '.join([f"'{h}'" for h in header_row if h])
                raise UserError(f"Required column '{required_name}' not found in your Excel file.\nAvailable columns: {available_columns}")
        
        return column_indices

    def _process_excel_data(self, sheet, column_indices):
        """Process Excel data and return a dictionary of default_code to quantity"""
        excel_data = defaultdict(float)
        processed_rows = 0
        
        for row_no, row in enumerate(sheet.iter_rows(min_row=2), start=2):  # Start from row 2 (after header)
            try:
                line = []
                for cell in row:
                    if cell.value is None:
                        line.append('')
                    elif isinstance(cell.value, (int, float)):
                        line.append(str(int(cell.value)) if cell.value == int(cell.value) else str(cell.value))
                    else:
                        line.append(str(cell.value).strip())

                if all(not cell for cell in line):
                    continue

                default_code = line[column_indices['default_code']] if column_indices['default_code'] < len(line) else ''
                quantity = line[column_indices['quantity']] if column_indices['quantity'] < len(line) else ''

                if not default_code or not quantity:
                    _logger.warning(f'Empty default_code or quantity in row {row_no}, skipping')
                    continue

                try:
                    quantity = float(quantity)
                    excel_data[default_code] += quantity
                    processed_rows += 1
                except ValueError:
                    _logger.warning(f'Invalid quantity value in row {row_no}: {quantity}, skipping')
                    continue

            except Exception as e:
                _logger.error(f'Error processing row {row_no}: {str(e)}')
                raise UserError(f'Error processing row {row_no}: {str(e)}')

        if processed_rows == 0:
            raise UserError('No valid data rows found in the Excel file.')

        return excel_data, processed_rows

    def _create_moves_and_lines(self, excel_data):
        """Create moves and move lines based on Excel data"""
        # Delete existing moves
        existing_moves = self.picking_id.move_ids_without_package
        if existing_moves:
            existing_moves.unlink()
            _logger.info(f'Deleted {len(existing_moves)} existing moves')

        # Get products by default_code
        products = self.env['product.product'].search([('default_code', 'in', list(excel_data.keys()))])
        product_by_code = {p.default_code: p for p in products}

        # Create moves
        moves_to_create = []
        for default_code, quantity in excel_data.items():
            if default_code in product_by_code:
                product = product_by_code[default_code]
                moves_to_create.append({
                    'name': f'Import {default_code}',
                    'product_id': product.id,
                    'product_uom_qty': quantity,
                    'product_uom': product.uom_id.id,
                    'picking_id': self.picking_id.id,
                    'location_id': self.picking_id.location_id.id,
                    'location_dest_id': self.picking_id.location_dest_id.id,
                })
            else:
                _logger.warning(f'Product with default_code {default_code} not found')

        # Create moves
        created_moves = self.env['stock.move'].create(moves_to_create)
        _logger.info(f'Created {len(created_moves)} new moves')

        # Create move lines
        move_lines_to_create = []
        for move in created_moves:
            move_lines_to_create.append({
                'move_id': move.id,
                'product_id': move.product_id.id,
                'quantity': move.product_uom_qty,
                'product_uom_id': move.product_id.uom_id.id,
                'location_id': self.picking_id.location_id.id,
                'location_dest_id': self.picking_id.location_dest_id.id,
            })

        # Create move lines
        created_lines = self.env['stock.move.line'].create(move_lines_to_create)
        _logger.info(f'Created {len(created_lines)} new move lines')

        return created_moves, created_lines

    def import_serials(self):
        """Main method to import data from Excel file"""
        self.ensure_one()
        
        # Validate file
        self._validate_file(self.move_file)

        fp = None
        workbook = None
        try:
            # Open Excel file
            fp = tempfile.NamedTemporaryFile(delete=False, suffix=".xlsx")
            fp.write(binascii.a2b_base64(self.move_file))
            fp.seek(0)
            workbook = openpyxl.load_workbook(fp.name, data_only=True, read_only=True)
            sheet = workbook.active

            # Process Excel data
            column_indices = self._get_column_indices(sheet)
            excel_data, processed_rows = self._process_excel_data(sheet, column_indices)

            # Create moves and lines
            created_moves, created_lines = self._create_moves_and_lines(excel_data)

            # Build summary message
            summary_lines = ["Stock Import Summary"]
            summary_lines.append("")
            summary_lines.append("Success:")
            for move in created_moves:
                product_name = move.product_id.name
                default_code = move.product_id.default_code
                quantity = move.product_uom_qty
                summary_lines.append(f"- {product_name} (default_code: {default_code}): {quantity} units")

            # Add totals
            summary_lines.append("")
            summary_lines.append(f"Total: {len(created_lines)} lines created for {len(created_moves)} products.")

            # Add message to chatter
            self.picking_id.message_post(body="\n".join(summary_lines))

            # Success message with summary
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': 'Import Successful',
                    'message': "\n".join(summary_lines),
                    'type': 'success',
                    'sticky': True,
                }
            }

        except Exception as e:
            _logger.error('Error importing data: %s', str(e))
            raise UserError('Error importing data: %s' % str(e))
        finally:
            # Cleanup
            if workbook:
                workbook.close()
            if fp:
                fp.close()
                try:
                    os.unlink(fp.name)
                except:
                    pass 