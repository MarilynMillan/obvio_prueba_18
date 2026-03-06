from odoo import models, fields

class ResPartnerBank(models.Model):
    _inherit = 'res.partner.bank'

    pdf_attachment = fields.Binary(string="Archive PDF")
    pdf_filename = fields.Char(string="Attach Bank PDF")