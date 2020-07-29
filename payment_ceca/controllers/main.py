# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import http
from odoo.http import request


class PaymentTransacionCecaController(http.Controller):

    @http.route(['/payment_transaction/ceca/action_run'],
                type='http', auth='public', methods=['GET'],
                website=True)
    def payment_transaction_ceca_action_run(self, **post):
        request.env['payment.transaction'].sudo().cron_sqs_ceca_action_run()
        return request.render('website.404')
