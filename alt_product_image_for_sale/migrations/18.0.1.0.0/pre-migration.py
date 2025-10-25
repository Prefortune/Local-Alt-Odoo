# -*- coding: utf-8 -*-

def migrate(cr, version):
    """
    Add missing fields to sale_order table
    """
    # List of fields to check and add
    fields_to_add = [
        ('alt_print_image', 'boolean DEFAULT true'),
        ('alt_image_sizes', 'varchar DEFAULT \'image_small\''),
        ('alt_hide_summary_in_quote', 'boolean DEFAULT false')
    ]
    
    for field_name, field_type in fields_to_add:
        # Check if the column already exists
        cr.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'sale_order' 
            AND column_name = %s
        """, (field_name,))
        
        if not cr.fetchone():
            # Add the column if it doesn't exist
            cr.execute("""
                ALTER TABLE sale_order 
                ADD COLUMN {} {}
            """.format(field_name, field_type))
            print("Added {} column to sale_order table".format(field_name))
        else:
            print("Column {} already exists in sale_order table".format(field_name)) 