from odoo import models, fields, api
import pytz

class MailMessage(models.Model):
    _inherit = 'mail.message'

    def unlink(self):
        records_to_delete = self.env['mail.message']
        for record in self:
            # We only track project task messages
            if record.model != 'project.task':
                records_to_delete |= record
                continue

            if "Borrado por" in (record.body or "") and 'color: lightgray' in (record.body or ""):
                records_to_delete |= record
                continue

            user_name = self.env.user.name

            # Get user timezone or UTC
            user_tz = pytz.timezone(self.env.user.tz or 'UTC')
            now_utc = fields.Datetime.now()
            local_dt = pytz.utc.localize(now_utc).astimezone(user_tz)
            current_time = local_dt.strftime('%Y-%m-%d %H:%M:%S')

            original_body = record.body or ""

            new_body = f"""
                <div style="color: lightgray;">
                    <i>Borrado por {user_name} a las {current_time}:</i><br/>
                    {original_body}
                </div>
            """
            super(MailMessage, record).write({'body': new_body})

        if records_to_delete:
            return super(MailMessage, records_to_delete).unlink()
        return True

    def write(self, vals):
        if 'body' in vals:
            user_name = self.env.user.name

            user_tz = pytz.timezone(self.env.user.tz or 'UTC')
            now_utc = fields.Datetime.now()
            local_dt = pytz.utc.localize(now_utc).astimezone(user_tz)
            current_time = local_dt.strftime('%Y-%m-%d %H:%M:%S')

            for record in self:
                # We only track project task messages
                if record.model != 'project.task':
                    continue

                original_body = record.body or ""
                new_content = vals.get('body') or ""

                # If the message is being marked as deleted or already has edit history,
                # we just want to save the new content but we could append the new edit history if they edit it again.
                # However, the frontend editor will load the entire HTML including the old edit history block.
                # When the user modifies it and saves, 'new_content' contains the new text + the OLD edit history block.
                # We want to keep appending history, but it might get messy.
                # The prompt says: "si es editar la actividad que quede lo que edito y lo actual".
                # For simplicity and correctness, if it already has "Editado por", we still let them save the new content.
                # We can try to extract just the original text before the old history, but that's complex HTML parsing.
                # Since the old edit history is part of new_content now, we can just save new_content.
                if "Borrado por" not in new_content and "Editado por" not in new_content:
                    edited_body = f"""
                        <div>{new_content}</div>
                        <div style="color: lightgray; margin-top: 10px; border-top: 1px solid #eee; padding-top: 5px;">
                            <i>Editado por {user_name} a las {current_time}:</i><br/>
                            <del>{original_body}</del>
                        </div>
                    """
                    super(MailMessage, record).write({'body': edited_body})
                else:
                    # Save the new content (which already contains the historical tracking block)
                    super(MailMessage, record).write({'body': new_content})

            project_task_records = self.filtered(lambda r: r.model == 'project.task')
            other_records = self - project_task_records

            vals_without_body = {k: v for k, v in vals.items() if k != 'body'}
            if vals_without_body and project_task_records:
                super(MailMessage, project_task_records).write(vals_without_body)

            if other_records:
                super(MailMessage, other_records).write(vals)

            return True

        return super(MailMessage, self).write(vals)
