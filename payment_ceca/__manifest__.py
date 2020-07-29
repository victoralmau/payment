# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

{
    "name": "Ceca Payment Acquirer",
    "version": "12.0.1.0.0",
    "category": "Sales Management",
    "website": "https://nodrizatech.com/",
    "author": "Odoo Nodriza Tech (ONT), "
              "Odoo Community Association (OCA)",
    "license": "AGPL-3",
    "external_dependencies": {
        "python": ["boto3"],
    },
    "depends": ["website_sale_management"],
    "data": [
        "data/ir_cron.xml",
        "views/ceca.xml",
        "views/payment_acquirer_view.xml",
        "data/payment_ceca.xml"
    ],
    "installable": True
}
