def create_attribute_if_not_exists(self, attribute_name):
    attribute_data = self.env['product.attribute'].search([('name', '=', attribute_name)])

    if not attribute_data:
        create_attribute = self.env['product.attribute'].create({'name': attribute_name})
        return create_attribute.id
    else:
        return attribute_data.id


def create_value_if_not_exists(self, attribute_id, attribute_value):
    value_data = self.env['product.attribute.value'].search([
        ('attribute_id', '=', attribute_id),
        ('name', '=', attribute_value)
    ])

    if not value_data:
        create_value = self.env['product.attribute.value'].create({
            'attribute_id': attribute_id,
            'name': attribute_value
        })
        return create_value.id
    else:
        return value_data.id


    # def sync_product(self, products):
    #     product_template = self.env['product.template']

    #     for product in products:
    #         product_id = product['id']
    #         product_name = product['title']
    #         product_type = product['product_type']

    #         find_exists = product_template.search([('shopify_product_id', '=', product_id)])

    #         product_dict = {
    #             'name': product_name,
    #             'detailed_type': 'product',
    #             'shopify_product_id':product_id
    #         }

    #         attribute_line_data = {}
    #         attr_id_list = []
    #         ex_val_ids = []
    #         for attr in product['options']:
    #             is_create = True
    #             update_val_ids = []
    #             val_array = []

    #             attribute_name = attr['name']
    #             values_str = ', '.join(attr['values'])

    #             if attribute_name != "Title":
    #                 attribute_id = self.create_attribute_if_not_exists(attribute_name)
    #                 attr_id_list.append(attribute_id)

    #                 if attribute_id not in attribute_line_data:
    #                     attribute_line_data[attribute_id] = []

    #                 if ',' in values_str:
    #                     values = [value.strip() for value in values_str.split(',')]
    #                 else:
    #                     values = [values_str]

    #                 for attribute_value in values:
    #                     value_id = self.create_value_if_not_exists(attribute_id, attribute_value)

    #                     attribute_line_data[attribute_id].append(value_id)
    #                     ex_val_ids.append(value_id)
    #                     update_val_ids.append(value_id)
    #                 val_array = update_val_ids
                        

    #             attribute_line_ids = [
    #                 (0, 0, {'attribute_id': attr_id, 'value_ids': [(6, 0, attr_values)]})
    #                 for attr_id, attr_values in attribute_line_data.items()
    #             ]

    #             if attribute_line_ids:
    #                 product_dict['attribute_line_ids'] = attribute_line_ids
            
            
    #             if find_exists:
    #                 is_create = False
    #                 existing_attr_line_id = find_exists.attribute_line_ids
    #                 if len(existing_attr_line_id) >= 1:
    #                     for exist_line in existing_attr_line_id:               
    #                         existing_attr_temp_val_data = self.env['product.template.attribute.line'].search([('attribute_id', '=', attribute_id),('product_tmpl_id', '=', find_exists.id)])
                            
    #                         if existing_attr_temp_val_data:
    #                             for at_val in val_array:
    #                                 existing_attr_temp_val_data.write({'attribute_id': attribute_id, 'value_ids': [(4, at_val)] })
    #                             product_dict['attribute_line_ids'] = []             
    #                         else:
    #                             new_attr = []
    #                             new_attr_data = (0, 0, {'attribute_id': attribute_id, 'value_ids': [(6, 0, val_array)]})
    #                             new_attr.append(new_attr_data)
    #                             product_dict['attribute_line_ids'] = new_attr
    #                     product_update = find_exists.write(product_dict)
    #                 else:
    #                     if attribute_line_ids:
    #                         product_dict['attribute_line_ids'] = attribute_line_ids
    #                     _logger.info(product_dict)
    #                     product_update = find_exists.write(product_dict)
    #             _logger.info(product_update)
    #             _logger.info(find_exists)


    #         if is_create:
    #             created_product = product_template.create(product_dict)      
def sync_product(self, products):
    product_template = self.env['product.template']

    for product in products:
        product_id = product['id']
        product_name = product['title']
        product_type = product['product_type']

        find_exists = product_template.search([('shopify_product_id', '=', product_id)])

        product_dict = {
            'name': product_name,
            'detailed_type': 'product',
            'shopify_product_id': product_id
        }

        attribute_line_data = {}
        ex_val_ids = []

        for attr in product['options']:
            attribute_name = attr['name']
            values = [value.strip() for value in attr['values']]
            
            if attribute_name == "Title":
                continue

            attribute_id = self.create_attribute_if_not_exists(attribute_name)

            attribute_line_data[attribute_id] = [self.create_value_if_not_exists(attribute_id, value) for value in values]
            ex_val_ids.extend(attribute_line_data[attribute_id])

        attribute_line_ids = [
            (0, 0, {'attribute_id': attr_id, 'value_ids': [(6, 0, attr_values)]})
            for attr_id, attr_values in attribute_line_data.items()
        ]

        if attribute_line_ids:
            product_dict['attribute_line_ids'] = attribute_line_ids

        if find_exists:
            existing_attr_line_id = find_exists.attribute_line_ids

            if existing_attr_line_id:
                for attr_id, val_array in attribute_line_data.items():
                    existing_attr_temp_val_data = self.env['product.template.attribute.line'].search([
                        ('attribute_id', '=', attr_id),
                        ('product_tmpl_id', '=', find_exists.id)
                    ])

                    if existing_attr_temp_val_data:
                        existing_attr_temp_val_data.write({'attribute_id': attr_id, 'value_ids': [(4, val) for val in val_array]})
                        product_dict['attribute_line_ids'] = []
                    else:
                        new_attr_data = (0, 0, {'attribute_id': attr_id, 'value_ids': [(6, 0, val_array)]})
                        product_dict['attribute_line_ids'] = [new_attr_data]

                product_update = find_exists.write(product_dict)
            else:
                if attribute_line_ids:
                    product_dict['attribute_line_ids'] = attribute_line_ids

                product_update = find_exists.write(product_dict)
        else:
            product_template.create(product_dict)

            
          


            
                  
                      

