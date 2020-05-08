# -*- coding: utf-8 -*-
import hashlib
from datetime import datetime

from odoo import models, fields, api, tools

import logging
_logger = logging.getLogger(__name__)

class AcquirerCeca(models.Model):
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

    provider = fields.Selection(selection_add=[('ceca', 'Ceca')])
    ceca_acquirer_bin = fields.Char('Ceca Acquirer Bin', required_if_provider='ceca')
    ceca_merchant_id = fields.Char('Ceca Merchant Id', required_if_provider='ceca')
    ceca_terminal_id = fields.Char('Ceca Terminal Id', required_if_provider='ceca')
    ceca_business_name = fields.Char('Ceca Business Name', required_if_provider='ceca')
    ceca_encriptation_key = fields.Char('Ceca Encriptation Key', required_if_provider='ceca')
    ceca_exponente = fields.Char('Ceca Exponente', required_if_provider='ceca')
    ceca_tipo_moneda = fields.Char('Ceca Tipo Moneda', required_if_provider='ceca')    

    @api.model
    def _get_website_url(self):
        return self.env['ir.config_parameter'].get_param('web.base.url')
      
    @api.multi
    def ceca_form_generate_values(self, values):
        self.ensure_one()
        ceca_values = dict(values)                        
        #vars
        base_url = self._get_website_url()                        
        urltpv = self._get_ceca_urls(self.environment)['ceca_form_url']
        MerchantID = str(self.ceca_merchant_id)
        AcquirerBIN = str(self.ceca_acquirer_bin)
        TerminalID = str(self.ceca_terminal_id)
        Exponente = str(self.ceca_exponente)
        TipoMoneda = str(self.ceca_tipo_moneda)        
        #url_ok = str(base_url)+'/payment/ceca/ok'
        #url_nok = str(base_url)+'/payment/ceca/ko'        
        url_ok = str(base_url)+values['return_url']+'?payment_ok=1'
        url_nok = str(base_url)+values['return_url']+'?payment_ko=1'
        Num_operacion = values['reference']
        #importe
        amount_split = str(values['amount']).split('.')
        Importe = str(amount_split[0])+str(amount_split[1])
        #Fix ad 0 final
        if len(amount_split[1])==1:
            Importe = str(Importe)+'0'        
        #others
        Idioma = 1
        Pago_soportado = 'SSL'
        Cifrado = 'SHA2'
        #get_order_id
        if Num_operacion=='/':        
            return_url = str(values['return_url'])
            return_url = return_url.replace('/quote/', '')            
            return_url_split = return_url.split('/')
            
            sale_order_ids = self.env['sale.order'].search([('id', '=', str(return_url_split[0]))])
            if len(sale_order_ids)>0:
                sale_order_id = sale_order_ids[0]
                Num_operacion = sale_order_id.name
        #Num_operacion
        Num_operacion += '-'+str(datetime.today().strftime("%H_%I_%S"))                                        
        #clave
        Clave = str(self.ceca_encriptation_key)
        string_to_sign = str(Clave)+str(MerchantID)+str(AcquirerBIN)+str(TerminalID)+str(Num_operacion)+str(Importe)+str(TipoMoneda)+str(Exponente)+str(Cifrado)+str(url_ok)+str(url_nok)
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
    
    @api.one
    def action_confirm_amount(self):
        _logger.info('action_confirm_amount')