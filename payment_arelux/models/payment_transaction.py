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
        #return
        return return_object