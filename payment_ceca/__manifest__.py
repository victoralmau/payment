# -*- coding: utf-8 -*-
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
{
    'name': 'Ceca Payment Acquirer',
    'version': '10.0.1.0.0',    
    'author': 'Odoo Nodriza Tech (ONT)',
    'website': 'https://nodrizatech.com/',
    'category': 'Tools',
    'license': 'AGPL-3',
    'depends': ['payment', 'ont_base_payment', 'website_portal_sale'],    
    'data': [
        'data/ir_cron.xml',
        'views/ceca.xml',
        'views/payment_acquirer.xml',
        'data/payment_ceca.xml'
    ],
    'installable': True,
    'auto_install': False,    
}