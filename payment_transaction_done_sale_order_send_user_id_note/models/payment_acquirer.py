# -*- coding: utf-8 -*-
from odoo import api, models, fields
from odoo.exceptions import Warning, ValidationError

import logging
_logger = logging.getLogger(__name__)

class PaymentAcquirer(models.Model):
    _inherit = 'payment.acquirer'
    
    done_sale_order_user_id_note = fields.Boolean(
        default=False,
        string='Notificacion al comercial',
        help='Crea una nota interna en el pedido al comercial'
    )