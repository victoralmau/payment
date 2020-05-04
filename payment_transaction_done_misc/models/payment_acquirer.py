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
    done_sale_order_user_id_note = fields.Boolean(
        default=False,
        string='Notificacion al comercial',
        help='Crea una nota interna en el pedido al comercial'
    )
    done_account_journal_id_account_payment = fields.Many2one(
        comodel_name='account.journal',
        string='Diario pagos',
        help='Diario de pago contra el que se crearan los pagos de las transacciones hechas'
    )
    done_account_journal_id_account_payment_method = fields.Many2one(
        comodel_name='account.payment.method',
        domain=[('payment_type', '=', 'inbound')],
        string='Metodo pago (account.payment)',
        help='Metodo de pago usado en el account.payment'
    )