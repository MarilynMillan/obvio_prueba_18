from odoo import models, api, _

class MailMessage(models.Model):
    _inherit = 'mail.message'

    def write(self, vals):
        if 'body' in vals:
            for message in self:
                # If the body is being modified, leave a log note about the edit
                # We only track manual messages or comments attached to a model
                if message.model and message.res_id and message.message_type in ('comment', 'notification'):
                    # To avoid recursion or breaking if the model does not exist
                    try:
                        record = self.env[message.model].browse(message.res_id).exists()
                        if record and hasattr(record, 'message_post'):
                            old_body = message.body
                            new_body = vals.get('body')
                            if old_body != new_body:
                                log_msg = _("Log Note Edited by %s:<br/><b>Old:</b> %s<br/><b>New:</b> %s") % (
                                    self.env.user.name, old_body, new_body
                                )
                                # Add message_type='notification' or subtype_id to avoid triggering
                                # normal email notifications just for editing a log
                                record.message_post(body=log_msg, subtype_xmlid='mail.mt_note')
                    except Exception:
                        pass
        return super(MailMessage, self).write(vals)

    def unlink(self):
        # We don't want to log a deleted message if the parent record is also being deleted.
        # This prevents creating orphaned messages.
        if self.env.context.get('is_unlinking_parent'):
            return super(MailMessage, self).unlink()

        for message in self:
            # If a message is deleted, leave a log note about the deletion
            if message.model and message.res_id and message.message_type in ('comment', 'notification'):
                try:
                    record = self.env[message.model].browse(message.res_id).exists()
                    if record and hasattr(record, 'message_post'):
                        # Check if the record is being unlinked
                        # We cannot post to a record that is being deleted.
                        # However, since we don't always have 'is_unlinking_parent' context, we do a best-effort.
                        log_msg = _("Log Note Deleted by %s:<br/><b>Content:</b> %s") % (
                            self.env.user.name, message.body
                        )
                        record.message_post(body=log_msg, subtype_xmlid='mail.mt_note')
                except Exception:
                    pass
        return super(MailMessage, self).unlink()
