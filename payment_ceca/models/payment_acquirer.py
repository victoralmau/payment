# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
import hashlib
from datetime import datetime

from odoo import models, fields, api

import logging
_logger = logging.getLogger(__name__)


class PaymentAcquirer(models.Model):
    _inherit = 'payment.acquirer'

    def _get_ceca_urls(self, environment):
        if environment == 'prod':
            return {
                'ceca_form_url':
                'https://pgw.ceca.es/tpvweb/tpv/compra.action'
            }
        else:
            return {
                'ceca_form_url':
                'https://tpv.ceca.es/tpvweb/tpv/compra.action'
            }

    provider = fields.Selection(
        selection_add=[('ceca', 'Ceca')]
    )
    ceca_acquirer_bin = fields.Char(
        string='Ceca Acquirer Bin',
        required_if_provider='ceca'
    )
    ceca_merchant_id = fields.Char(
        string='Ceca Merchant Id',
        required_if_provider='ceca'
    )
    ceca_terminal_id = fields.Char(
        string='Ceca Terminal Id',
        required_if_provider='ceca'
    )
    ceca_business_name = fields.Char(
        string='Ceca Business Name',
        required_if_provider='ceca'
    )
    ceca_encriptation_key = fields.Char(
        string='Ceca Encriptation Key',
        required_if_provider='ceca'
    )
    ceca_exponente = fields.Char(
        string='Ceca Exponente',
        required_if_provider='ceca'
    )
    ceca_tipo_moneda = fields.Char(
        string='Ceca Tipo Moneda',
        required_if_provider='ceca'
    )

    @api.model
    def _get_website_url(self):
        return self.env['ir.config_parameter'].get_param('web.base.url')

    @api.multi
    def ceca_form_generate_values(self, values):
        ceca_values = dict(values)
        # vars
        base_url = self._get_website_url()
        urltpv = self._get_ceca_urls(self.environment)['ceca_form_url']
        MerchantID = str(self.ceca_merchant_id)
        AcquirerBIN = str(self.ceca_acquirer_bin)
        TerminalID = str(self.ceca_terminal_id)
        Exponente = str(self.ceca_exponente)
        TipoMoneda = str(self.ceca_tipo_moneda)
        url_ok = str(base_url)+values['return_url']+'?payment_ok=1'
        url_ok = "%s%s?payment_ok=1" % (
            base_url,
            values['return_url']
        )
        url_nok = "%s%s?payment_ko=1" % (
            base_url,
            values['return_url']
        )
        Num_operacion = values['reference']
        # importe
        amount_split = str(values['amount']).split('.')
        Importe = str(amount_split[0])+str(amount_split[1])
        # Fix ad 0 final
        if len(amount_split[1]) == 1:
            Importe = str(Importe)+'0'
        # others
        Idioma = 1
        Pago_soportado = 'SSL'
        Cifrado = 'SHA2'
        # get_order_id
        if Num_operacion == '/':
            return_url = str(values['return_url'])
            return_url = return_url.replace('/quote/', '')
            return_url_split = return_url.split('/')

            sale_order_ids = self.env['sale.order'].search(
                [
                    ('id', '=', str(return_url_split[0]))
                ]
            )
            if sale_order_ids:
                Num_operacion = sale_order_ids[0].name
        # Num_operacion
        Num_operacion += '-'+str(datetime.today().strftime("%H_%I_%S"))
        # clave
        Clave = str(self.ceca_encriptation_key)
        string_to_sign = '%s%s%s%s%s%s%s%s%s%s%s' % (
            Clave,
            MerchantID,
            AcquirerBIN,
            TerminalID,
            Num_operacion,
            Importe,
            TipoMoneda,
            Exponente,
            Cifrado,
            url_ok,
            url_nok
        )
        Firma = hashlib.sha256(string_to_sign.encode()).hexdigest()
        ceca_values.update({
            'urltpv': urltpv,
            'merchantid': MerchantID,
            'acquirerbin': AcquirerBIN,
            'terminalid': TerminalID,
            'exponente': Exponente,
            'tipomoneda': TipoMoneda,
            'url_ok': url_ok,
            'url_nok': url_nok,
            'num_operacion': Num_operacion,
            'importe': Importe,
            'idioma': Idioma,
            'pago_soportado': Pago_soportado,
            'descripcion': values['reference'],
            'firma': Firma,
            'cifrado': Cifrado
        })
        return ceca_values

    @api.multi
    def ceca_get_form_action_url(self):
        return self._get_ceca_urls(self.environment)['ceca_form_url']

    @api.multi
    def action_confirm_amount(self):
        _logger.info('action_confirm_amount')
