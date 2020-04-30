# -*- coding: utf-8 -*-
from openerp import api, models, fields
from openerp.exceptions import Warning, ValidationError

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
            if self.acquirer_id.done_sale_order_user_id_note==True:
                if self.sale_order_id.id>0:
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
        #return
        return return_object