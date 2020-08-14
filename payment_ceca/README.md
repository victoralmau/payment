Se realiza la funcionalidad correspondiente para añadir el modo de pago Ceca (payment.acquire) nuevo.

Este addon requiere website_quote_arelux  (que logra mostrar el botón de Pagar en el presupuesto online SOLO cuando está marcado el check de ‘Proforma’ y está seleccionado el modo de pago ‘TPV Virtual’)

Adicionalmente a esto, las respuestas de CECA van a payment_transaction/ceca POST.

Adicionalmente, con el addon account_arelux  y el parámetro payment_transaction_done_mail_template_id se enviará un email de pago OK al cliente a través del presupuesto Y se generará una nota interna indicando el importe pagado Y colocando esa nota interna como destacada para el comercial del presupuesto.

 
## odoo.conf
- #payment_ceca
- sqs_payment_transaction_ceca_url=https://sqs.eu-west-1.amazonaws.com/381857310472/arelux-odoo_dev-command-payment-transaction-ceca

Es imprescindible que la Regla de registro en Odoo “Access own payment transaction only” esté inactiva puesto que de lo contrario, solo podríamos encontrar transacciones de clientes con el comercial de webservice. > Probablemente al funcionar por SQS esto ya no sea necesario.

## Crones:

### SQS Payment Transaction Ceca Action Run 

Frecuencia: 1 vez cada 10 minutos

Descripción: 

Consulta los SQS:

nombre | version
--- | ---
arelux-odoo-command-payment-transaction-ceca | Prod
arelux-odoo_dev-command-payment-transaction-ceca | Dev

y realiza las operaciones de creación/actualización respecto a los elementos del modelo: payment.transaction
