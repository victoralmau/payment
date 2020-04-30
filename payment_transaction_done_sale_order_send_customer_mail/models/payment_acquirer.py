# -*- coding: utf-8 -*-
from odoo import api, models, fields
from odoo.exceptions import Warning, ValidationError

import logging
_logger = logging.getLogger(__name__)

class PaymentAcquirer(models.Model):
    _inherit = 'payment.acquirer'
    
    done_sale_order_customer_mail_template_id = fields.Many2one(
        comodel_name='mail.template',
        domain=[('model_id.model', '=', 'payment.transaction')],
        string='Plantilla email cliente',
        help='Email que se enviara al cliente cuando la transaccion se complete y este vinculada con un pedido de venta'
    )