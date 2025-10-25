from odoo import fields, models,api

import logging
import re
from odoo.exceptions import UserError, ValidationError

class MailMessage(models.Model):
    _inherit ="mail.message"

    active = fields.Boolean(string="Active",default=True)    

   
          
class ProductReview(models.Model):
    _name = 'product.review'

    name=fields.Char(string="Name")
    pf_customer_id= fields.Many2one(comodel_name='res.partner',string="Customer",store=True, readonly=False,requried=True)

    pf_review = fields.Char(string="Review")

    pf_rating = fields.Selection([('0','none'),('1','none'),('2','none'),('3','ko'),('4','ok'),('5','top')], string="Rating",store=True) 

    pf_product_review_line_ids = fields.One2many('product.review.line','pf_product_review_id',string="Product Review Line")    

    pf_is_active = fields.Boolean(string="Publish",default=True)

    pf_product_ids = fields.Many2many('product.product', string='Products')

    pf_service_state = fields.Selection([('publish', 'Publish'),
        ('unpublish', 'Unpublish')],string='Service Status', group_expand='_group_expand_states',default='publish',track_visibility='always',compute='_compute_service_state',store=True)
    
    pf_rating_int = fields.Float(
        string="Average Rating",
        store=True,group_operator="avg",compute="_compute_rating_int")


    @api.depends('pf_is_active')
    def _compute_service_state(self):
        for record in self:
            record.pf_service_state = 'publish' if record.pf_is_active else 'unpublish'
    
    def _group_expand_states(self, states, domain, order):
        return [key for key, val in type(self).pf_service_state.selection]
    
    @api.onchange('pf_rating_int')
    def _onchange_rating_int(self):
            if self.pf_rating_int == 5:
                self.pf_rating = '5'
            elif self.pf_rating_int == 4:
                self.pf_rating = '4'
            elif self.pf_rating_int == 3:
                self.pf_rating = '3'
            elif self.pf_rating_int == 2:
                self.pf_rating = '2'
            elif self.pf_rating_int == 1:
                self.pf_rating = '1'
            elif self.pf_rating_int == 0:
                self.pf_rating = '0'
            else:
                raise ValidationError('you can not give pf_rating_int more than 5')
            
            

    @api.depends('pf_rating')
    def _compute_rating_int(self):
        for record in self:
            rating_map = {
                '0': 0, 
                '1': 1, 
                '2': 2,  
                '3': 3, 
                '4': 4, 
                '5': 5  
            }
            record.pf_rating_int = rating_map.get(record.pf_rating, 0) 

    @staticmethod
    def _map_rating_to_int(pf_rating):
        rating_map = {
            '0': 0,
            '1': 1,
            '2': 2,
            '3': 3,
            '4': 4,
            '5': 5
        }
        return rating_map.get(pf_rating, 0)
  

    def write(self, vals):   
        res = super(ProductReview, self).write(vals)                   
        rating_text_mapping = {
        5: 'top',  
        4: 'ok',  
        3: 'ok',    
        2: 'ko',   
        1: 'ko',    # 1 -> Dissatisfied
        0: 'none',  # 0 -> No Rating yet
    }
        if 'pf_product_ids' in vals or 'pf_rating' in vals or 'pf_is_active' in vals:
            chatter_message_ids=[]
            for record in self.pf_product_ids: 
                product_tmpl_obj=  record.product_tmpl_id               
                print("\n\n\n............................self....",product_tmpl_obj,self.id,product_tmpl_obj.products_review_line_ids.mapped('pf_product_review_id').ids)                
                product_review_line = product_tmpl_obj.products_review_line_ids.filtered(lambda line: line.pf_product_review_id.id == self.id)
                print("\n\n\n...........product_review_line....",product_review_line,product_review_line.pf_message_id)
                if product_review_line:
                    if product_review_line.pf_product_tmpl_id.id ==  product_review_line.pf_message_id.res_id:
                        print("\n\n\n............................self....",self.id,product_tmpl_obj.products_review_line_ids.mapped('pf_product_review_id').ids)
                        if self.pf_is_active:
                            product_review_line.pf_message_id.write({                            
                                'body': self.pf_review, 
                                'author_id': self.pf_customer_id.id,     
                                'active':self.pf_is_active  
                            })
                            for rating in product_review_line.pf_message_id.rating_ids:
                                rating.write({                                    
                                    'rating':str(float(self.pf_rating))
                                })
                            review_line = {
                                'pf_product_review_id':self.id,
                                'pf_product_tmpl_id':product_tmpl_obj.id,
                                'pf_rating_int': int(self.pf_rating_int),
                                'pf_rating': self.pf_rating,             
                                'pf_review':re.sub(r'<p>|</p>', '', self.pf_review),
                                'pf_customer_id': self.pf_customer_id.id,
                                'pf_is_active':True,
                                'pf_message_id':product_review_line.pf_message_id.id
                            }
                            product_review_line.sudo().write(review_line)
                        else:                                
                            product_review_line.pf_message_id.write({'active':False})      
                            product_review_line.sudo().write({'pf_is_active':False})
                        print("\n\n\n...product_review_line.pf_message_id....",product_review_line.pf_message_id.active)
                    else:
                        if isinstance(self.pf_rating_int, (int, float)) and self.pf_rating_int in rating_text_mapping:
                            rating_texts = rating_text_mapping[self.pf_rating_int]    

                            new_rating = self.env['rating.rating'].sudo().create({
                            'res_id':product_tmpl_obj.id,  
                            'res_model': 'product.template',  
                            'partner_id': self.pf_customer_id.id,  
                            'rating': int(self.pf_rating_int),                          
                            'consumed': True,

                            })

                            print("\n\n\\n...................pf_rating_int....",new_rating)
                        # Create a chatter message with the review and pf_rating_int
                            chatter_message = self.env['mail.message'].sudo().create({
                                'model': 'product.template',
                                'res_id': product_tmpl_obj.id, 
                                'message_type': 'comment', 
                                'author_id': self.pf_customer_id.id,
                                'pf_rating_int':int(self.pf_rating_int),            
                                'body': self.pf_review, 
                                'active':self.pf_is_active,
                                'rating_ids': [(6, 0, [new_rating.id])]  
                            })
                            review_line = {
                                'pf_product_review_id':self.id,
                                'pf_product_tmpl_id':product_tmpl_obj.id,
                                'pf_rating_int': int(self.pf_rating_int),
                                'pf_review':re.sub(r'<p>|</p>', '', self.pf_review),
                                'pf_rating': self.pf_rating, 
                                'pf_customer_id': self.pf_customer_id.id,
                                'pf_is_active':True,
                                'pf_message_id':chatter_message.id,
                                'pf_is_active':self.pf_is_active
                            }
                            product_message_line_review = self.env['product.review.line'].with_context({'post_msg':False}).sudo().create(review_line)
                            print("\n\n\n.............product_message_line_review............",product_message_line_review)
                else:
                    if isinstance(self.pf_rating_int, (int, float)) and self.pf_rating_int in rating_text_mapping:
                        rating_texts = rating_text_mapping[self.pf_rating_int]    

                        new_rating = self.env['rating.rating'].sudo().create({
                        'res_id':product_tmpl_obj.id,  
                        'res_model': 'product.template',  
                        'partner_id': self.pf_customer_id.id,  
                        'rating': int(self.pf_rating_int),                          
                        'consumed': True,

                        })

                        print("\n\n\\n...................pf_rating_int....",new_rating)
                    # Create a chatter message with the review and pf_rating_int
                        chatter_message = self.env['mail.message'].sudo().create({
                            'model': 'product.template',
                            'res_id': product_tmpl_obj.id, 
                            'message_type': 'comment', 
                            'author_id': self.pf_customer_id.id,                         
                            'body': self.pf_review, 
                            'active':self.pf_is_active,
                            'rating_ids': [(6, 0, [new_rating.id])]  
                        })
                        review_line = {
                            'pf_product_review_id':self.id,
                            'pf_product_tmpl_id':product_tmpl_obj.id,
                            'pf_rating_int': int(self.pf_rating_int),
                            'pf_review':re.sub(r'<p>|</p>', '', self.pf_review),
                            'pf_customer_id': self.pf_customer_id.id,
                            'pf_is_active':True,
                            'pf_message_id':chatter_message.id,
                            'pf_is_active':self.pf_is_active,
                            'pf_rating': self.pf_rating, 
                        }
                        product_message_line_review = self.env['product.review.line'].with_context({'post_msg':False}).sudo().create(review_line)
                        print("\n\n\n.............product_message_line_review............",product_message_line_review)                                                            
        return res

    def create_review_lines_from_chatter(self, rating_key):
        product_rating = {
            5 : 'top',
            4 : 'ok',
            3 : 'ko',
            2 : 'none',
            1 : 'none'
        }
        pf_rating_int = product_rating.get(rating_key)       
        return pf_rating_int

class ProductReviewLine(models.Model):
    _name="product.review.line"

    pf_product_review_id = fields.Many2one('product.review',string="Product Review")

    pf_product_tmpl_id = fields.Many2one('product.template',string="Product")

    pf_message_id = fields.Many2one('mail.message', string='Chatter Message', help='Original message from chatter')    

    pf_customer_id= fields.Many2one(comodel_name='res.partner',string="Customer",store=True, readonly=False,requried=True)

    pf_review = fields.Char(string="Review")

    pf_rating = fields.Selection([('0','none'),('1','none'),('2','none'),('3','ko'),('4','ok'),('5','top')], string="Rating",store=True) 

    pf_is_active = fields.Boolean(string="Publish",default=True)
    pf_rating_int = fields.Integer(
        string="Average Rating",
        store=True,group_operator="avg",compute="_compute_rating_int")
    
    @api.depends('pf_rating')
    def _compute_rating_int(self):
        for record in self:
            rating_map = {
                '0': 0, 
                '1': 1, 
                '2': 2,  
                '3': 3, 
                '4': 4, 
                '5': 5  
            }
            record.pf_rating_int = rating_map.get(record.pf_rating, 0) 

class RatingModel(models.Model):
    _inherit = "rating.rating"

    @api.depends('res_model', 'res_id')
    def _compute_res_name(self):
        for rating in self:
            if rating.res_model and rating.res_id:
                name = self.env[rating.res_model].sudo().browse(rating.res_id).display_name
                rating.res_name = name or f'{rating.res_model}/{rating.res_id}'
