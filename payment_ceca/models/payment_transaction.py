# -*- coding: utf-8 -*-
import base64
import json
import urllib
from datetime import datetime

from odoo import models, fields, api, tools
from odoo.addons.payment.models.payment_acquirer import ValidationError
from odoo.tools.float_utils import float_compare
from odoo import http

import pytz

import boto3
from botocore.exceptions import ClientError

import logging
_logger = logging.getLogger(__name__)

class TxCeca(models.Model):
    _inherit = 'payment.transaction'

    # Ceca status
    _ceca_valid_tx_status = list(range(0, 100))
    _ceca_pending_tx_status = list(range(101, 203))
    _ceca_cancel_tx_status = [912, 9912]
    _ceca_error_tx_status = list(range(9064, 9095))

    ceca_txnid = fields.Char('Transaction ID')

    def merchant_params_json2dict(self, data):
        parameters = data.get('Ds_MerchantParameters', '').decode('base64')
        return json.loads(parameters)

    # --------------------------------------------------
    # FORM RELATED METHODS
    # --------------------------------------------------

    @api.model
    def _ceca_form_get_tx_from_data(self, data):
        _logger.info('_ceca_form_get_tx_from_data')
        """ Given a data dict coming from ceca, verify it and
        find the related transaction record. """
        parameters = data.get('Ds_MerchantParameters', '')
        parameters_dic = json.loads(base64.b64decode(parameters))
        reference = urllib.unquote(parameters_dic.get('Ds_Order', ''))
        pay_id = parameters_dic.get('Ds_AuthorisationCode')
        shasign = data.get('Ds_Signature', '').replace('_', '/').replace('-', '+')
        test_env = http.request.session.get('test_enable', False)
        if not reference or not pay_id or not shasign:
            error_msg = 'Ceca: received data with missing reference' \
                ' (%s) or pay_id (%s) or shashign (%s)' % (reference,
                                                           pay_id, shasign)
            if not test_env:
                _logger.info(error_msg)
                raise ValidationError(error_msg)
            http.OpenERPSession.tx_error = True
        tx = self.search([('reference', '=', reference)])
        if not tx or len(tx) > 1:
            error_msg = 'Ceca: received data for reference %s' % (reference)
            if not tx:
                error_msg += '; no order found'
            else:
                error_msg += '; multiple order found'
            if not test_env:
                _logger.info(error_msg)
                raise ValidationError(error_msg)
            http.OpenERPSession.tx_error = True
        if tx and not test_env:
            # verify shasign
            shasign_check = tx.acquirer_id.sign_parameters(
                tx.acquirer_id.ceca_secret_key, parameters)
            if shasign_check != shasign:
                error_msg = (
                    'Ceca: invalid shasign, received %s, computed %s, '
                    'for data %s' % (shasign, shasign_check, data)
                )
                _logger.info(error_msg)
                raise ValidationError(error_msg)
        return tx

    @api.multi
    def _ceca_form_get_invalid_parameters(self, data):
        _logger.info('_ceca_form_get_invalid_parameters')
        invalid_parameters = []
        test_env = http.request.session.get('test_enable', False)
        parameters_dic = self.merchant_params_json2dict(data)
        if (self.acquirer_reference and parameters_dic.get('Ds_Order')) != self.acquirer_reference:
            invalid_parameters.append(('Transaction Id', parameters_dic.get('Ds_Order'), self.acquirer_reference))

        # check what is buyed
        if (float_compare(float(parameters_dic.get('Ds_Amount', '0.0')) / 100, self.amount, 2) != 0):
            invalid_parameters.append(('Amount', parameters_dic.get('Ds_Amount'), '%.2f' % self.amount))
        if invalid_parameters and test_env:
            return []
        return invalid_parameters

    @api.multi
    def _ceca_form_validate(self, data):
        _logger.info('_ceca_form_validate')
        parameters_dic = self.merchant_params_json2dict(data)
        status_code = int(parameters_dic.get('Ds_Response', '29999'))
        if status_code in self._ceca_valid_tx_status:
            self.write({
                'state': 'done',
                'ceca_txnid': parameters_dic.get('Ds_AuthorisationCode'),
                'state_message': _('Ok: %s') % parameters_dic.get('Ds_Response'),
            })
            if self.acquirer_id.send_quotation:
                self.sale_order_id.force_quotation_send()
            return True
        if status_code in self._ceca_pending_tx_status:
            # 'Payment error: code: %s.'
            self.write({
                'state': 'pending',
                'ceca_txnid': parameters_dic.get('Ds_AuthorisationCode'),
                'state_message': _('Error: %s (%s)') % (
                    parameters_dic.get('Ds_Response'),
                    parameters_dic.get('Ds_ErrorCode')
                ),
            })
            return True
        if status_code in self._ceca_cancel_tx_status:
            # 'Payment error: bank unavailable.'
            self.write({
                'state': 'cancel',
                'ceca_txnid': parameters_dic.get('Ds_AuthorisationCode'),
                'state_message': _('Bank Error: %s (%s)') % (
                    parameters_dic.get('Ds_Response'),
                    parameters_dic.get('Ds_ErrorCode')
                ),
            })
            return True
        else:
            error = _('Ceca: feedback error %s (%s)') % (
                parameters_dic.get('Ds_Response'),
                parameters_dic.get('Ds_ErrorCode')
            )
            _logger.info(error)
            self.write({
                'state': 'error',
                'ceca_txnid': parameters_dic.get('Ds_AuthorisationCode'),
                'state_message': error,
            })
            return False

    @api.model
    def form_feedback(self, data, acquirer_name):
        _logger.info('form_feedback')
        res = super(TxCeca, self).form_feedback(data, acquirer_name)
        try:
            tx_find_method_name = '_%s_form_get_tx_from_data' % acquirer_name
            if hasattr(self, tx_find_method_name):
                tx = getattr(self, tx_find_method_name)(data)
            _logger.info(
                '<%s> transaction processed: tx ref:%s, tx amount: %s',
                acquirer_name, tx.reference if tx else 'n/a',
                tx.amount if tx else 'n/a')
                
            if tx and tx.sale_order_id:
                amount_matches = (
                    tx.sale_order_id.state in ['draft', 'sent'] and
                    float_compare(tx.amount, tx.sale_order_id.amount_total, 2) == 0)
                if amount_matches:
                    if tx.state == 'done':
                        _logger.info(
                            '<%s> transaction completed, confirming order '
                            '%s (ID %s)', acquirer_name,
                            tx.sale_order_id.name, tx.sale_order_id.id)
                        if not self.env.context.get('bypass_test', False):
                            tx.sale_order_id.with_context(
                                send_email=True).action_confirm()
                    elif (tx.state != 'cancel' and
                            tx.sale_order_id.state == 'draft'):
                        _logger.info('<%s> transaction pending, sending '
                                     'quote email for order %s (ID %s)',
                                     acquirer_name, tx.sale_order_id.name,
                                     tx.sale_order_id.id)
                        if not self.env.context.get('bypass_test', False):
                            tx.sale_order_id.force_quotation_send()
                else:
                    _logger.warning('<%s> transaction MISMATCH for order '
                                    '%s (ID %s)', acquirer_name,
                                    tx.sale_order_id.name,
                                    tx.sale_order_id.id)
        except Exception:
            _logger.exception(
                'Fail to confirm the order or send the confirmation email%s',
                tx and ' for the transaction %s' % tx.reference or '')
        return res

    @api.model
    def cron_sqs_ceca_action_run(self):
        _logger.info('cron_sqs_ceca_action_run')

        sqs_url = tools.config.get('sqs_payment_transaction_ceca_url')
        AWS_ACCESS_KEY_ID = tools.config.get('aws_access_key_id')
        AWS_SECRET_ACCESS_KEY = tools.config.get('aws_secret_key_id')
        AWS_SMS_REGION_NAME = tools.config.get('aws_region_name')
        # boto3
        sqs = boto3.client(
            'sqs',
            region_name=AWS_SMS_REGION_NAME,
            aws_access_key_id=AWS_ACCESS_KEY_ID,
            aws_secret_access_key=AWS_SECRET_ACCESS_KEY
        )
        # Receive message from SQS queue
        total_messages = 10
        while total_messages > 0:
            response = sqs.receive_message(
                QueueUrl=sqs_url,
                AttributeNames=['All'],
                MaxNumberOfMessages=10,
                MessageAttributeNames=['All']
            )
            if 'Messages' in response:
                total_messages = len(response['Messages'])
            else:
                total_messages = 0
            # continue
            if 'Messages' in response:
                for message in response['Messages']:
                    # message_body
                    message_body = json.loads(message['Body'])
                    # fix message
                    if 'Message' in message_body:
                        message_body = json.loads(message_body['Message'])
                    # result_message
                    result_message = {
                        'statusCode': 200,
                        'return_body': 'OK',
                        'message': message_body
                    }
                    # fields_need_check
                    fields_need_check = ['Importe', 'Num_operacion', 'Referencia']
                    for field_need_check in fields_need_check:
                        if field_need_check not in message_body:
                            result_message['statusCode'] = 500
                            result_message['return_body'] = {'error': 'No existe el campo ' + str(field_need_check)}
                    # operations
                    if result_message['statusCode'] == 200:
                        # amount
                        amount_pre = (float(str(message_body['Importe']))) / 100
                        amount = "{0:.2f}".format(amount_pre)
                        # reference
                        reference = message_body['Num_operacion'].split('-')[0]
                        #payment_transaction_id_vals
                        current_date = datetime.now(pytz.timezone('Europe/Madrid'))
                        payment_transaction_id_vals = {
                            'state': 'done',
                            'amount': amount,
                            'acquirer_reference': str(message_body['Referencia']),
                            'date_validate': str(current_date.strftime("%Y-%m-%d %H:%M:%S"))
                        }
                        #search
                        payment_transaction_ids = self.env['payment.transaction'].sudo().search(
                            [
                                ('state', '=', 'draft'),
                                ('reference', '=', str(reference)),
                                ('acquirer_id.provider', '=', 'ceca'),
                            ]
                        )
                        if len(payment_transaction_ids)==0:
                            result_message['statusCode'] = 500
                            result_message['return_body'] = {'error': 'RARO - NO HAY PAYMENT_TRANSACTION - REPETIDO?'}
                        #data
                        result_message['data'] = payment_transaction_id_vals
                        _logger.info(result_message)
                        # create-write
                        if result_message['statusCode'] == 200:  # error, data not exists
                            payment_transaction_id = payment_transaction_ids[0]
                            #write
                            payment_transaction_id.write(payment_transaction_id_vals)
                        # remove_message
                        if result_message['statusCode'] == 200:
                            response_delete_message = sqs.delete_message(
                                QueueUrl=sqs_url,
                                ReceiptHandle=message['ReceiptHandle']
                            )