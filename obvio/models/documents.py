from odoo import api, fields, models, _

class IrAttachment(models.Model):
    _inherit = 'ir.attachment'

    def write(self, vals):
        res = super(IrAttachment, self).write(vals)
        # Odoo 18 refactored documents, documents.document logic is essentially handled in ir.attachment.
        # So we ensure the ir.attachment is correctly renamed and vice versa if needed,
        # but standard Odoo 18 automatically handles attachment renaming if handled here.
        return res

class DocumentsDocument(models.Model):
    _inherit = 'documents.document'

    name = fields.Char(translate=True)

    def write(self, vals):
        res = super(DocumentsDocument, self).write(vals)
        if 'name' in vals:
            for doc in self:
                if hasattr(doc, 'attachment_id') and doc.attachment_id:
                    doc.attachment_id.sudo().write({'name': vals['name']})
        return res