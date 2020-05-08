# -*- coding: utf-8 -*-
{
    'name': 'Payment transaction Done misc',
    'version': '12.0.1.0.0',    
    'author': 'Odoo Nodriza Tech (ONT)',
    'website': 'https://nodrizatech.com/',
    'category': 'Tools',
    'license': 'AGPL-3',
    'depends': ['payment', 'sale', 'mail'],    
    'data': [
        'views/payment_acquirer.xml',
    ],
    'installable': True,
    'auto_install': False,    
}