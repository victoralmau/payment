# -*- coding: utf-8 -*-
from odoo import models, fields, api, tools

import logging
_logger = logging.getLogger(__name__)

class PaymentTransaction(models.Model):
    _inherit = 'payment.transaction'

    @api.model
    def action_payment_transaction_done_error(self, error):
        _logger.info(error)