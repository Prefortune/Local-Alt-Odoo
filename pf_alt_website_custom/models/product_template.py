from odoo import fields, models,api
from odoo.addons.http_routing.models.ir_http import slug
import re
class ProductTemplate(models.Model):
    _inherit='product.template'

    product_bundle_ids = fields.Many2many('product.bundle.template', string="Product Bundle")
    products_review_line_ids = fields.One2many('product.review.line','pf_product_tmpl_id',string="Product Review")
    product_slug = fields.Char(string="product Slug")



    chatter_reviews = fields.One2many(
        'mail.message','res_id', 
        domain=[('model', '=', 'product.template'), ('message_type', '=', 'comment')], 
        string='Chatter Reviews'
    )

    chatter_messages = fields.One2many('mail.message','res_id', 
        domain=[('model', '=', 'product.template')], 
        string='Chatter Reviews'
    )
    # Add new type
    type = fields.Selection(
        selection_add=[('bundle', 'Bundle')],
        ondelete={'bundle': 'cascade'}
    )

    # Extend 'detailed_type' field
    detailed_type = fields.Selection(
        selection_add=[
            ('bundle', 'Bundle')
        ],
        ondelete={'bundle': 'cascade'}
    )

    @api.depends('chatter_messages')
    def _compute_message_string(self):
          for record in self:
            comment_messages = record.chatter_messages.filtered(lambda m: m.message_type == 'comment')
            def remove_p_tags(text):
                text_without_p = re.sub(r'<p>|</p>', '', text)
                return text_without_p
            record.message_string = '\n'.join(remove_p_tags(message.body) for message in comment_messages)
                 


    def message_post(self, **kwargs):
        result = super(ProductTemplate, self).message_post(**kwargs)
        self.create_review_lines_from_chatter(result.id)
        return result

    def create_review_lines_from_chatter(self,msg_id):
        product_rating ={
        'top' : '5',
        'ok' : '3',
        'ko' : '2',
        'ko' : '1'
    }
        for product in self:             
            chatter_messages = self.env['mail.message'].sudo().search([
                    ('model', '=', 'product.template'),
                    ('res_id', '=', product.id),
                    ('id', '=', msg_id),
                ])

            for message in chatter_messages:
                rating_chatter = message.rating_ids.mapped('rating')
                messages = product.products_review_line_ids.mapped('pf_message_id')
                if msg_id not in messages.ids:
                    review_vals={
                        'name':product.name,
                        'pf_customer_id': message.author_id.id,
                        'pf_review':re.sub(r'<p>|</p>', '', message.body),
                        'pf_is_active':True,
                        'pf_rating_int': int(rating_chatter[0]),
                        'pf_rating':str(int(rating_chatter[0])),
                        'pf_product_ids': product.product_variant_ids.ids,
                        'pf_product_review_line_ids':[(0,0,{
                            'pf_product_tmpl_id':product.id,
                            'pf_rating_int': int(rating_chatter[0]),
                            'pf_rating':str(int(rating_chatter[0])),
                            'pf_review':re.sub(r'<p>|</p>', '', message.body),
                            'pf_customer_id': message.author_id.id,
                            'pf_is_active':True,
                            'pf_message_id':msg_id
                        })]
                    }
                    product_message_review = self.env['product.review'].with_context({'post_msg':False}).sudo().create(review_vals)
                    print("\n\\nn..............product_message_review.........",product_message_review)
                  



    @api.model_create_multi
    def create(self, vals_list):                   
        res = super(ProductTemplate, self).create(vals_list)
        for rec in res:
            total_price = 0.0  # Initialize total price
            rec_obj=[]
            if rec.product_bundle_ids:
                if rec.combo_ids:
                    for combo in rec.combo_ids:    
                        product_objs=combo.combo_line_ids.mapped('product_id')  
                        if product_objs:             
                            for bundle_line in rec.product_bundle_ids:
                                if bundle_line.product_id.id not in product_objs.ids:
                                    pos_combo_line={                                
                                        'combo_line_ids':[(0, 0, {
                                        'product_id': bundle_line.product_id.id,
                                        'combo_price': bundle_line.pf_combo_price,                                        
                                        }
                                        )]
                                    },   
                                    combo.write({pos_combo_line})
                else:
                    line=[]
                    if rec.product_bundle_ids:
                        for bundle_line in rec.product_bundle_ids:    
                            total_price = total_price + (bundle_line.product_id.lst_price * bundle_line.pf_qty)                  
                            pos_combo_line=(0, 0, {
                                'product_id': bundle_line.product_id.id,
                                'combo_price': bundle_line.pf_combo_price,                               
                                }
                                )                            
                            line.append(pos_combo_line)

                    obj=self.env['pos.combo'].sudo().create({'name':rec.name+'combo','combo_line_ids':line})
                    rec_obj.append(obj.id)
            if rec:
                rec.sudo().write({'combo_ids':[rec_obj]})
            if total_price > 0:
                rec.sudo().write({'standard_price': total_price,'list_price': total_price})

        return res
    
    def write(self, vals):             
        res=super(ProductTemplate, self).write(vals)
        if self.product_bundle_ids:
            if self.combo_ids:
                for combo in self.combo_ids:    
                    product_objs=combo.combo_line_ids.mapped('product_id')  
                    if product_objs:             
                        for bundle_line in self.product_bundle_ids:
                            if bundle_line.product_id.id not in product_objs.ids:
                                pos_combo_line={                                
                                    'combo_line_ids':[(0, 0, {
                                    'product_id': bundle_line.product_id.id,
                                    'combo_price': bundle_line.pf_combo_price,                                  
                                    }
                                    )]
                                } 
                                print("\n\n\n.......................................pos_combo_line",pos_combo_line,combo)
                                combo.sudo().write(pos_combo_line)     
        return res



class AltAdsProductBundleTemplate(models.Model):
    _name = "product.bundle.template"
    _rec_name = "product_id"

    product_id = fields.Many2one("product.product", string="Product", required=True)
    pf_combo_price = fields.Float("Price Extra", default=0.0)
    pf_lst_price = fields.Float("Original Price", related="product_id.lst_price")
    pf_qty = fields.Integer("Quantity", default=1)
    pf_total_price = fields.Float("Total Price", compute="_compute_pf_total_price", store=True)

    @api.depends('product_id', 'pf_qty')
    def _compute_pf_total_price(self):
        for record in self:
            if record.product_id and record.pf_qty > 0:
                record.pf_total_price = record.product_id.lst_price * record.pf_qty
            else:
                record.pf_total_price = 0.0