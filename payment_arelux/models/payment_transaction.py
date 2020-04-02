# -*- coding: utf-8 -*-
from openerp import api, models, fields
from openerp.exceptions import Warning, ValidationError

import logging
_logger = logging.getLogger(__name__)

class PaymentTransaction(models.Model):
    _inherit = 'payment.transaction'
    
    @api.one
    def write(self, vals):        
        #auto-add mail_message comment
        mail_message_notification_need = False
        if 'state' in vals:
            if vals['state']=='done' and self.state!='done':
                if self.sale_order_id.id>0:
                    mail_message_notification_need = True                    
        #write
        return_object = super(PaymentTransaction, self).write(vals)
        #mail_message_notification_need
        if mail_message_notification_need==True:
            mail_message_vals = {
                'subtype_id': 2,
                'message_type': 'notification',
                'body': 'Pago confirmado por un importe de '+str(self.amount)+str(self.currency_id.symbol)+ ' desde '+str(self.acquirer_id.name),
                'model': 'sale.order',
                'res_id': self.sale_order_id.id,
                'record_name': self.sale_order_id.name                                                                        
            }
            #add_auto_starred
            if self.sale_order_id.user_id.id>0:
                mail_message_vals['starred_partner_ids'] = [[6, False, [self.sale_order_id.user_id.partner_id.id]]]
            #create
            if self.sale_order_id.user_id.id>0:
                mail_message_obj = self.env['mail.message'].sudo(self.sale_order_id.user_id.id).create(mail_message_vals)
            else:
                mail_message_obj = self.env['mail.message'].sudo().create(mail_message_vals)
            #mail.compose.message (sale.order)
            payment_transaction_done_mail_template_id = int(self.env['ir.config_parameter'].sudo().get_param('payment_transaction_done_mail_template_id'))
            if payment_transaction_done_mail_template_id>0:        
                if self.sale_order_id.user_id.id>0:
                    mail_compose_message_obj = self.env['mail.compose.message'].sudo(self.sale_order_id.user_id.id).create({})
                else:                
                    mail_compose_message_obj = self.env['mail.compose.message'].sudo().create({})
                
                return_mail_compose_message_obj = mail_compose_message_obj.onchange_template_id(payment_transaction_done_mail_template_id, 'comment', 'sale.order', self.sale_order_id.id)
                mail_body = return_mail_compose_message_obj['value']['body']                          
                #replace
                if '[payment_transaction_amount]' in mail_body: 
                    mail_body = mail_body.replace('[payment_transaction_amount]', str(self.amount))
                
                if '[payment_transaction_currency_id_symbol]' in mail_body: 
                    mail_body = mail_body.replace('[payment_transaction_currency_id_symbol]', str(self.currency_id.symbol))                
                
                if '[payment_transaction_acquirer_id_name]' in mail_body:
                    mail_body = mail_body.replace('[payment_transaction_acquirer_id_name]', str(self.acquirer_id.name))
                            
                #update                                    
                mail_compose_message_obj.composition_mode = 'comment'
                mail_compose_message_obj.model = 'sale.order'
                mail_compose_message_obj.res_id = self.sale_order_id.id
                mail_compose_message_obj.template_id = payment_transaction_done_mail_template_id
                mail_compose_message_obj.body = mail_body
                mail_compose_message_obj.subject = return_mail_compose_message_obj['value']['subject']
                mail_compose_message_obj.record_name = self.sale_order_id.name  
                #send_mail_action
                mail_compose_message_obj.send_mail_action()                        
        #return
        return return_object