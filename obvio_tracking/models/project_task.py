from odoo import models, fields, api, _

class ProjectTask(models.Model):
    _inherit = 'project.task'

    def write(self, vals):
        # Tracking canceled tasks and tasks marked as done losing info.
        # If moving to done or cancel, we might want to ensure we log who was assigned
        for task in self:
            new_state = vals.get('state', getattr(task, 'state', None))
            new_stage_id = vals.get('stage_id', task.stage_id.id)

            # Detect change to "done" or "canceled" state (Odoo 16+ uses specific states like '1_done', '1_canceled', or '03_approved', etc.)
            # We also check if user_ids are being cleared (vals.get('user_ids') = False or empty)
            if 'state' in vals or 'stage_id' in vals or 'user_ids' in vals:
                users_names = task.user_ids.mapped('name')
                if users_names:
                    task.message_post(
                        body=_('Modification on task. Assigned users at this time: %s') % ', '.join(users_names),
                        subtype_xmlid='mail.mt_note'
                    )

        return super(ProjectTask, self).write(vals)

    def unlink(self):
        for task in self:
            # When a task is deleted, it leaves no trace by default because the record is gone.
            # To leave a trace, we log it on the project before deleting it.
            if task.project_id:
                log_msg = _("Task '%s' was deleted by %s. It was assigned to: %s. Stage: %s, State: %s") % (
                    task.name,
                    self.env.user.name,
                    ', '.join(task.user_ids.mapped('name')) if task.user_ids else 'Unassigned',
                    task.stage_id.name if task.stage_id else 'None',
                    getattr(task, 'state', 'None')
                )
                task.project_id.message_post(body=log_msg, subtype_xmlid='mail.mt_note')
        return super(ProjectTask, self.with_context(is_unlinking_parent=True)).unlink()
