from odoo import api, fields, models, _

class ResPartnerID(models.Model):
    _inherit = 'res.partner'


    alias_name = fields.Char(string='Short name')
    is_operator = fields.Boolean(string='Operator', help='Check if this contact is an operator')
    codigo_operator = fields.Char(string='Operator code')
    customer_is = fields.Boolean(string='Customer',help='Check if this contact is a customer')