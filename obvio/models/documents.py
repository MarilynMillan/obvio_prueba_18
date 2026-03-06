from odoo import api, fields, models, _

class DocumentsDocument(models.Model):
    _inherit = 'documents.document'

    name = fields.Char(translate=True)