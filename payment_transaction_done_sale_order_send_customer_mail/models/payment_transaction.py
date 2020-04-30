# -*- coding: utf-8 -*-
from odoo import api, models, fields
from odoo.exceptions import Warning, ValidationError

import logging
_logger = logging.getLogger(__name__)

class PaymentTransaction(models.Model):
    _inherit = 'payment.transaction'
    
    @api.one
    def write(self, vals):        
        #state_done_now
        state_done_now = False
        if 'state' in vals:
            if vals['state']=='done' and self.state!='done':
                if self.sale_order_id.id>0:
                    state_done_now = True                    
        #write
        return_object = super(PaymentTransaction, self).write(vals)
        #operations
        if state_done_now==True:
            if self.acquirer_id.done_sale_order_customer_mail_template_id.id>0:
                if self.sale_order_id.id>0:
                    #send_mail
                    if self.sale_order_id.user_id.id>0:
                        mail_compose_message_obj = self.env['mail.compose.message'].sudo(self.sale_order_id.user_id.id).create({})
                    else:                
                        mail_compose_message_obj = self.env['mail.compose.message'].sudo().create({})
                    #onchange_template_id
                    return_mail_compose_message_obj = mail_compose_message_obj.onchange_template_id(self.acquirer_id.done_sale_order_customer_mail_template_id.id, 'comment', 'payment.transaction', self.id)
                    mail_body = return_mail_compose_message_obj['value']['body']                                            
                    #update                                    
                    mail_compose_message_obj.composition_mode = 'comment'
                    mail_compose_message_obj.model = 'sale.order'
                    mail_compose_message_obj.res_id = self.sale_order_id.id
                    mail_compose_message_obj.record_name = self.sale_order_id.name                
                    mail_compose_message_obj.template_id = self.acquirer_id.done_sale_order_customer_mail_template_id.id
                    mail_compose_message_obj.body = mail_body
                    mail_compose_message_obj.subject = return_mail_compose_message_obj['value']['subject']                  
                    #send_mail_action
                    mail_compose_message_obj.send_mail_action()
        #return
        return return_object