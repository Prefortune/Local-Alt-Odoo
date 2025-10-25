# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
import re
from html import unescape
from odoo.exceptions import ValidationError


class Project(models.Model):
    _inherit="project.project"

    product_id = fields.Many2one('product.product', string='Add Services')

    pf_stage = fields.Selection([('new','New'),('bilable','Bilable'),('non_bilable','Non Bilable'),('internal','Internal')],string='stages',  group_expand='read_group_stage_ids')

    @api.model
    def read_group_stage_ids(self, states, domain, order):
        return [key for key, val in type(self).pf_stage.selection]

    def write(self, values):
        if ('stage_id' in values) or ('pf_stage' in values):
            approve_stages = self.env['project.project.stage'].sudo().search([('pf_is_approve_stage','=',True)])
            progress_stages = self.env['project.project.stage'].sudo().search([('pf_is_in_progress_stage','=',True)])
            if approve_stages and  progress_stages:
                for approve_stage in approve_stages:
                    if 'stage_id' in values:
                        if values['stage_id'] == approve_stage.id:                                             
                            values.update({
                                'pf_stage': 'new'
                            })
                        for progress_stage in progress_stages:
                            if values['stage_id'] == progress_stage.id:    
                                if self.pf_stage == 'new':    
                                    if (self.sale_order_id.id) or ('sale_order_id' in values):                                     
                                        values.update({
                                            'pf_stage': 'bilable'
                                        })
                                    else:
                                        values.update({
                                            'pf_stage': 'non_bilable'
                                        }) 

                if 'pf_stage' in values:
                    if progress_stages.id and ('pf_stage' in values) or self.pf_stage:
                        if values['pf_stage'] == 'bilable' or values['pf_stage'] == 'non_bilable' or self.pf_stage == 'new':                                                    
                                values.update({
                                'stage_id' : progress_stages.id
                            })
                                    
        res = super(Project, self).write(values)
        return res


class ProjectProjectStage(models.Model):
    _inherit = 'project.project.stage'

    pf_is_approve_stage = fields.Boolean(string='Approve Stage')
    pf_is_in_progress_stage=fields.Boolean(string='In Progress Stage')


class Task(models.Model):
    _inherit = 'project.task'

    is_paid_se = fields.Selection([('new','New'),('paid','Bilable'),('unpaid','Non Bilable'),('internal','Internal')],default="unpaid",string="Is bilable ?",group_expand='read_group_pf_stage')
    product_id = fields.Many2one('product.product', string='Add Services')
    pf_stage = fields.Selection([('new','New'),('bilable','Bilable'),('non_bilable','Non Bilable'),('internal','Internal')],string='stages',group_expand='read_group_pf_stage')

    def read_group_pf_stage(self, states, domain, order):
        return [key for key, val in type(self).is_paid_se.selection]


    # def write(self, values):
    #     if 'stage_id' in values:
    #         if self.stage_id.name == "new" or (self.stage_id.name == "New"):                                             
    #             values.update({
    #                 'pf_stage': 'new'
    #             })    
    #             if 'is_paid_se' in values:           
    #                 if values['is_paid_se'] == 'paid':                                                       
    #                     values.update({
    #                         'pf_stage': 'bilable'
    #                     })
    #                 else:
    #                     values.update({
    #                         'pf_stage': 'non_bilable'
    #                     })   
    #             else:
    #                 values.update({
    #                         'pf_stage': 'internal'
    #                     })                
    #     res = super(Task, self).write(values)
    #     return res

    def write(self, values):
        res = super(Task, self).write(values)

        for task in self:
            is_paid_se = task.is_paid_se

            if is_paid_se == 'paid':
                task.pf_stage = 'bilable'
            elif is_paid_se == 'unpaid':
                task.pf_stage = 'non_bilable'
            else:
                task.pf_stage == 'internal'

        return res
    
    def pf_open_task(self):
        print("\n\n\n.............self....",self)
        return {
            'type': 'ir.actions.act_window',
            'name': _('Task'),
            'res_model': 'project.task',
            'view_mode':'form',
            'res_id': self.id,           
        }
    
    @api.model_create_multi
    def create(self, vals_list):                   
        res = super(Task, self).create(vals_list)
        for rec in res:
            if rec.project_id.product_id and rec.product_id:
                order=self.env['sale.order'].sudo().search([('project_id','=',rec.product_id.id)],limit=1)
                if order:
                    order.write({
                        'order_line':[(0,0,{
                            'product_id': rec.product_id.id,
                            'name':rec.name,
                            'product_uom_qty': 1, 
                            'price_unit': rec.product_id.list_price,  # Default price
                            'product_uom': rec.product_id.uom_id.id,  # Unit of Measure 
                        })]
                    })
                    message = f"New order line added to Order {order.name}: {rec.product_id.name}"
                    self.env['mail.message'].create({
                        'message_type': 'notification',
                        'body': message,
                        'subject': 'Order Line Added',
                        'res_id': order.id,
                        'model': 'sale.order',
                    })

                    # Alternatively, you can use notify partners (e.g., assigned user)
                    if order.user_id:
                        order.user_id.notify_info(message)
        return res

    def write(self,vals):                
        res = super(Task, self).write(vals)
        for rec in self:
            if 'product_id' in vals:
                order=self.env['sale.order'].sudo().search([('project_id','=',rec.product_id.id)],limit=1)
                if order:
                    order.write({
                        'order_line':[(0,0,{
                            'product_id': rec.product_id.id,
                            'name':rec.name,
                            'product_uom_qty': 1,  # Default quantity
                            'price_unit': rec.product_id.list_price,  # Default price
                            'product_uom': rec.product_id.uom_id.id,  # Unit of Measure 
                        })]
                    })
                    message = f"New order line added to Order {order.name}: {rec.product_id.name}"
                    self.env['mail.message'].create({
                        'message_type': 'notification',
                        'body': message,
                        'subject': 'Order Line Added',
                        'res_id': order.id,
                        'model': 'sale.order',
                    })

                    # Alternatively, you can use notify partners (e.g., assigned user)
                    if order.user_id:
                        order.user_id.notify_info(message)
        return res

        


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    project_id = fields.Many2one('project.project', string='Project')

    @api.onchange('project_id')
    def _onchange_partner_id_add_order_line(self):
         if self.project_id.product_id: 
            self.order_line = [(5, 0, 0)]                   
            self.order_line = [(0, 0, {
                'product_id': self.project_id.product_id.id,
                'name': self.project_id.product_id.name,
                'product_uom_qty': 1,  
                'price_unit': self.project_id.product_id.list_price, 
                'product_uom': self.project_id.product_id.uom_id.id,
            })]   
            tasks = self.env['project.task'].search([('project_id', '=', self.project_id.id)])
            line_descriptions = []
            if tasks:
                for task in tasks:
                    if task.description:  
                        plain_text = re.sub(r'<[^>]*>', '', task.description)
                        plain_text = re.sub(r'\s+', ' ', plain_text)   
                        plain_text = unescape(plain_text).strip()          
                        if plain_text and not re.fullmatch(r"[0-9,]+", plain_text):  
                            line_descriptions.append(plain_text)  
                            self.order_line = [(0, 0, {
                            'product_id': task.product_id.id,
                            'name':plain_text,
                            'product_uom_qty': 1,  
                            'price_unit': task.product_id.list_price, 
                            'product_uom': task.product_id.uom_id.id, 
                        })] 

    @api.model
    def create(self, vals):
        if 'project_id' in vals:
            project_id = vals.get('project_id')
            if project_id:
                project = self.env['project.project'].browse(project_id)
                tasks = self.env['project.task'].search([('project_id', '=', project.id)])
                if tasks:
                    if not any(task.product_id and task.description for task in tasks):
                        raise ValidationError('Please assign product and description to tasks before creating a sale order.')
                else:
                    raise ValidationError('No the tasks is associated with selected project. Please create task before create sale order.')
                
        return super(SaleOrder, self).create(vals)



            


                