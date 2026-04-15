from odoo import models, fields, api
import pytz

# =========================
# CHATTER (mail.message)
# =========================
class MailMessage(models.Model):
    _inherit = 'mail.message'

   def unlink(self):
        """ Borrado lógico: Cambia el cuerpo y evita el borrado físico """
        task_messages = self.filtered(lambda r: r.model == 'project.task')
        other_messages = self - task_messages

        for record in task_messages:
            # Si ya está borrado (tiene el emoji), permitir el borrado real de la DB si se insiste
            if record.body and '🗑️' in str(record.body):
                other_messages |= record
                continue

            user_tz = pytz.timezone(self.env.user.tz or 'UTC')
            current_time = fields.Datetime.now().astimezone(user_tz).strftime('%Y-%m-%d %H:%M:%S')

            # Agregamos una clase CSS personalizada 'is_deleted_message' para ocultar el botón después
            new_body = f"""
                <div class="is_deleted_message" style="color: #666; text-decoration: line-through; opacity: 0.7; background: #f9f9f9; padding: 8px; border-radius: 4px;">
                    <small><i>🗑️ Eliminado por {self.env.user.name} el {current_time}:</i></small><br/>
                    {record.body or ''}
                </div>
            """
            super(MailMessage, record.with_context(skip_tracking=True)).write({'body': new_body})

        if other_messages:
            return super(MailMessage, other_messages).unlink()
        return True

    def write(self, vals):
        """ Trazabilidad de edición bloqueada si el mensaje ya fue eliminado """
        if 'body' in vals and vals.get('body') and not self._context.get('skip_tracking'):
            # MARCADO CRÍTICO: No puede ser un string vacío ""
            marker = ""
            
            for record in self:
                if record.model != 'project.task' or not record.body:
                    continue

                body_str = str(record.body)
                
                # BLOQUEO: Si el mensaje está borrado, no permitimos editar el body
                if '🗑️' in body_str or 'is_deleted_message' in body_str:
                    continue

                new_content = str(vals.get('body', ''))

                if marker in body_str:
                    parts = body_str.split(marker, 1)
                    old_content = parts[0]
                    history = parts[1]
                else:
                    old_content = body_str
                    history = ""

                if new_content.strip() == old_content.strip():
                    continue

                user_tz = pytz.timezone(self.env.user.tz or 'UTC')
                current_time = fields.Datetime.now().astimezone(user_tz).strftime('%Y-%m-%d %H:%M:%S')

                new_body = f"""{new_content}
{marker}
<div style="margin-top: 10px; border-top: 1px dashed #ddd; padding-top: 5px;">
    <div style="color: #555; font-size: 0.85em; background-color: #fcfcfc; padding: 5px; border-radius: 3px;">
        <i>✎ Editado por {self.env.user.name} el {current_time}:</i>
        <div style="color: #777; padding-left: 10px; font-style: italic;">{old_content}</div>
    </div>
    {history}
</div>"""
                super(MailMessage, record).write({'body': new_body})
            
            # Sacamos el body para que Odoo no intente escribirlo de nuevo
            vals.pop('body', None)

        return super(MailMessage, self).write(vals)


# =========================
# ACTIVIDADES (mail.activity)
# =========================
class MailActivity(models.Model):
    _inherit = 'mail.activity'

    def action_done(self):
        """ Cubre el botón 'Mark Done' directo del Chatter """
        return super(MailActivity, self.with_context(skip_cancel_log=True)).action_done()

    def action_feedback(self, feedback=False, attachment_ids=None, **kwargs):
        """ 
        Cubre el Wizard y botones con comentarios. 
        Usamos **kwargs para capturar argumentos extra como 'web_send_message' 
        y evitar el TypeError.
        """
        return super(MailActivity, self.with_context(skip_cancel_log=True)).action_feedback(
            feedback=feedback, 
            attachment_ids=attachment_ids, 
            **kwargs
        )

    def _action_done(self, feedback=False, attachment_ids=None):
        """ Método interno de finalización """
        return super(MailActivity, self.with_context(skip_cancel_log=True))._action_done(
            feedback=feedback, 
            attachment_ids=attachment_ids
        )

    def unlink(self):
        """ Solo registra la cancelación si NO es una finalización (Done) """
        if not self._context.get('skip_cancel_log'):
            for activity in self:
                if activity.res_model == 'project.task':
                    user_tz = pytz.timezone(self.env.user.tz or 'UTC')
                    current_time = fields.Datetime.now().astimezone(user_tz).strftime('%Y-%m-%d %H:%M:%S')

                    self.env['mail.message'].create({
                        'body': f"""
                            <div style="color: #666666; border-left: 3px solid #ccc; padding-left: 10px;">
                                <small><i>🗙 Actividad cancelada por {self.env.user.name} el {current_time}</i></small>
                                <br/><b>Asunto:</b> {activity.summary or activity.activity_type_id.name}
                                <br/><span style="font-size: 0.9em;">Nota: {activity.note or 'Sin nota'}</span>
                            </div>
                        """,
                        'model': activity.res_model,
                        'res_id': activity.res_id,
                        'message_type': 'notification',
                    })
        return super(MailActivity, self).unlink()