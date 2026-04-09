from odoo import _, api, models
from odoo.exceptions import AccessError


class AccountAnalyticLine(models.Model):
    _inherit = "account.analytic.line"

    def _is_project_user_restricted(self):
        user = self.env.user
        return user.has_group("project.group_project_user") and not user.has_group(
            "project.group_project_manager"
        )

    def _is_allowed_project_or_task(self, project_id, task_id, user):
        task = (
            self.env["project.task"].sudo().browse(task_id).exists()
            if task_id
            else self.env["project.task"]
        )
        project = (
            self.env["project.project"].sudo().browse(project_id).exists()
            if project_id
            else self.env["project.project"]
        )

        if task and not project:
            project = task.project_id

        if not task and not project:
            return False

        return bool(project) and project.user_id == user

    def _check_project_user_timesheet_access(self, vals_list=None, records=None):
        if not self._is_project_user_restricted():
            return

        user = self.env.user

        if vals_list:
            for vals in vals_list:
                project_id = vals.get("project_id")
                task_id = vals.get("task_id")
                if project_id is False:
                    project_id = None
                if task_id is False:
                    task_id = None
                if not self._is_allowed_project_or_task(project_id, task_id, user):
                    raise AccessError(
                        _(
                            "You can only manage timesheets on projects where you are the responsible."
                        )
                    )

        if records:
            for line in records:
                if not self._is_allowed_project_or_task(line.project_id.id, line.task_id.id, user):
                    raise AccessError(
                        _(
                            "You can only manage timesheets on projects where you are the responsible."
                        )
                    )

    @api.model_create_multi
    def create(self, vals_list):
        self._check_project_user_timesheet_access(vals_list=vals_list)
        return super().create(vals_list)

    def write(self, vals):
        if self._is_project_user_restricted():
            user = self.env.user
            for line in self:
                project_id = vals.get("project_id", line.project_id.id)
                task_id = vals.get("task_id", line.task_id.id)
                if project_id is False:
                    project_id = None
                if task_id is False:
                    task_id = None
                if not self._is_allowed_project_or_task(project_id, task_id, user):
                    raise AccessError(
                        _(
                            "You can only manage timesheets on projects where you are the responsible."
                        )
                    )
        return super().write(vals)

    def unlink(self):
        self._check_project_user_timesheet_access(records=self)
        return super().unlink()
