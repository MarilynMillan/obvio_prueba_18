from odoo import api, fields, models, _

class DocumentsDocument(models.Model):
    _inherit = 'documents.document'

    
    name = fields.Char(translate=True)

    def write(self, vals):
        if self.env.context.get('skip_attachment_sync'):
            return super(DocumentsDocument, self).write(vals)

        res = super(DocumentsDocument, self).write(vals)
        
        if 'name' in vals:
            for doc in self:
                # En Odoo 18, attachment_id es el campo clave
                if doc.attachment_id:
                    # Usamos with_context para evitar que el adjunto intente renombrar al documento de vuelta
                    doc.attachment_id.sudo().with_context(skip_document_sync=True).write({
                        'name': vals['name']
                    })
        return res

class IrAttachment(models.Model):
    _inherit = 'ir.attachment'

    def write(self, vals):
        if self.env.context.get('skip_document_sync'):
            return super(IrAttachment, self).write(vals)

        res = super(IrAttachment, self).write(vals)
        
        if 'name' in vals:
            for attachment in self:
                # Buscamos si este adjunto tiene un documento vinculado
                document = self.env['documents.document'].sudo().search([
                    ('attachment_id', '=', attachment.id)
                ], limit=1)
                if document:
                    document.with_context(skip_attachment_sync=True).write({
                        'name': vals['name']
                    })
        return res