from odoo import _, api, models, Command
from odoo.exceptions import AccessError, UserError


class ProjectImportGuardMixin(models.AbstractModel):
    _name = "project.import.guard.mixin"
    _description = "Project Import Guard Mixin"

    def _check_project_user_import_guard(self):
        user = self.env.user
        if user.has_group("project.group_project_user") and not user.has_group(
            "project.group_project_manager"
        ):
            raise UserError(
                _("Import is not allowed for Project/User on this model.")
            )


class ProjectProject(models.Model):
    _inherit = "project.project"

    def write(self, vals):
        alias_fields = {
            "alias_name",
            "alias_domain_id",
            "alias_contact",
            "alias_defaults",
            "alias_bounced_content",
        }
        if alias_fields.intersection(vals):
            user = self.env.user
            if user.has_group("project.group_project_user") and not user.has_group(
                "project.group_project_manager"
            ):
                forbidden = self.filtered(lambda p: p.user_id != user)
                if forbidden:
                    raise AccessError(
                        _(
                            "You can only edit the email alias on projects where you are the responsible."
                        )
                    )
        return super().write(vals)

    def load(self, fields, data):
        self.env["project.import.guard.mixin"]._check_project_user_import_guard()
        return super().load(fields, data)


class ProjectTask(models.Model):
    _inherit = "project.task"

    def _is_project_user_restricted(self):
        user = self.env.user
        return user.has_group("project.group_project_user") and not user.has_group(
            "project.group_project_manager"
        )

    def _check_project_user_task_project_access_on_create(self, vals_list):
        if not self._is_project_user_restricted():
            return

        user = self.env.user
        project_ids = {vals.get("project_id") for vals in vals_list if vals.get("project_id")}
        if not project_ids:
            return

        projects = self.env["project.project"].sudo().browse(list(project_ids)).exists()
        projects_by_id = {project.id: project for project in projects}
        for vals in vals_list:
            project_id = vals.get("project_id")
            if not project_id:
                continue
            project = projects_by_id.get(project_id)
            if not project or project.user_id != user:
                raise AccessError(
                    _(
                        "You can only create tasks in projects where you are the responsible."
                    )
                )

    def _check_project_user_task_project_access_on_write(self, vals):
        if not self._is_project_user_restricted():
            return
        if "project_id" not in vals:
            return

        new_project_id = vals.get("project_id")
        if not new_project_id:
            return

        project = self.env["project.project"].sudo().browse(new_project_id).exists()
        if not project or project.user_id != self.env.user:
            raise AccessError(
                _(
                    "You can only move tasks to projects where you are the responsible."
                )
            )

    def _is_user_task_manager(self, user):
        self.ensure_one()
        return self.project_id.user_id == user or user in self.user_ids

    def _is_user_task_manager_by_id(self, task_id, user):
        task = self.sudo().browse(task_id).exists()
        return bool(task) and (task.project_id.user_id == user or user in task.user_ids)

    def activity_schedule(self, act_type_xmlid="", date_deadline=None, summary="", note="", **act_values):
        user = self.env.user
        if user.has_group("project.group_project_user") and not user.has_group(
            "project.group_project_manager"
        ):
            forbidden_ids = [
                task_id for task_id in self.ids if not self._is_user_task_manager_by_id(task_id, user)
            ]
            if forbidden_ids:
                raise AccessError(
                    _(
                        "You can only schedule activities on tasks where you are the project responsible or an assignee."
                    )
                )
        return super().activity_schedule(
            act_type_xmlid=act_type_xmlid,
            date_deadline=date_deadline,
            summary=summary,
            note=note,
            **act_values,
        )

    def load(self, fields, data):
        self.env["project.import.guard.mixin"]._check_project_user_import_guard()
        return super().load(fields, data)

    @api.model_create_multi
    def create(self, vals_list):
        self._check_project_user_task_project_access_on_create(vals_list)
        return super().create(vals_list)

    def write(self, vals):
        self._check_project_user_task_project_access_on_write(vals)
        return super().write(vals)


class ProjectMilestone(models.Model):
    _inherit = "project.milestone"

    def load(self, fields, data):
        self.env["project.import.guard.mixin"]._check_project_user_import_guard()
        return super().load(fields, data)


class ProjectUpdate(models.Model):
    _inherit = "project.update"

    def load(self, fields, data):
        self.env["project.import.guard.mixin"]._check_project_user_import_guard()
        return super().load(fields, data)


class ProjectTaskType(models.Model):
    _inherit = "project.task.type"

    def _extract_project_ids_from_stage_vals(self, vals):
        commands = vals.get("project_ids")
        project_ids = set()
        if commands:
            for command in commands:
                if not isinstance(command, (list, tuple)) or not command:
                    continue
                operation = command[0]
                if operation == Command.SET:
                    project_ids.update(
                        pid for pid in (command[2] or []) if isinstance(pid, int) and not isinstance(pid, bool) and pid > 0
                    )
                elif operation == Command.LINK:
                    pid = command[1]
                    if isinstance(pid, int) and not isinstance(pid, bool) and pid > 0:
                        project_ids.add(pid)
                elif operation == Command.CLEAR:
                    project_ids.clear()
        if project_ids:
            return project_ids

        default_project_ids = self.env.context.get("default_project_ids")
        if isinstance(default_project_ids, int):
            if not isinstance(default_project_ids, bool) and default_project_ids > 0:
                return {default_project_ids}
            return set()
        if isinstance(default_project_ids, (list, tuple)):
            return {
                pid
                for pid in default_project_ids
                if isinstance(pid, int) and not isinstance(pid, bool) and pid > 0
            }

        default_project_id = self.env.context.get("default_project_id")
        if isinstance(default_project_id, int):
            if not isinstance(default_project_id, bool) and default_project_id > 0:
                return {default_project_id}
            return set()

        return set()

    def _check_project_user_stage_create_access(self, vals_list):
        user = self.env.user
        if not user.has_group("project.group_project_user") or user.has_group(
            "project.group_project_manager"
        ):
            return

        for vals in vals_list:
            project_ids = self._extract_project_ids_from_stage_vals(vals)
            personal_stage_owner = vals.get("user_id")
            if (
                not project_ids
                and isinstance(personal_stage_owner, int)
                and not isinstance(personal_stage_owner, bool)
                and personal_stage_owner == user.id
            ):
                # Opening "My Tasks" may create missing personal stages with no project link.
                continue
            if not project_ids:
                raise AccessError(
                    _(
                        "You can only create task stages for projects where you are the responsible."
                    )
                )
            projects = self.env["project.project"].sudo().browse(list(project_ids)).exists()
            if not projects or any(project.user_id != user for project in projects):
                raise AccessError(
                    _(
                        "You can only create task stages for projects where you are the responsible."
                    )
                )

    @api.model_create_multi
    def create(self, vals_list):
        self._check_project_user_stage_create_access(vals_list)
        return super().create(vals_list)


class MailMessage(models.Model):
    _inherit = "mail.message"

    _PROJECT_GUARDED_MODELS = {
        "project.project",
        "project.task",
        "project.milestone",
        "project.update",
    }

    def _is_project_user_restricted(self):
        user = self.env.user
        return user.has_group("project.group_project_user") and not user.has_group(
            "project.group_project_manager"
        )

    def _can_manage_project_related_record(self, model_name, res_id, user):
        if model_name not in self._PROJECT_GUARDED_MODELS:
            return True
        if not res_id:
            return False
        record = self.env[model_name].sudo().browse(res_id).exists()
        if not record:
            return False
        if model_name == "project.project":
            return record.user_id == user
        if model_name == "project.task":
            return record.project_id.user_id == user or user in record.user_ids
        return record.project_id.user_id == user

    def _check_project_user_message_manage_access(self, candidates):
        if not self._is_project_user_restricted():
            return
        user = self.env.user
        for model_name, res_id in candidates:
            if model_name not in self._PROJECT_GUARDED_MODELS:
                continue
            if not self._can_manage_project_related_record(model_name, res_id, user):
                raise AccessError(
                    _(
                        "You can only manage chatter messages on project records where you are the project responsible or task assignee."
                    )
                )

    @api.model_create_multi
    def create(self, vals_list):
        candidates = [
            (vals.get("model"), vals.get("res_id"))
            for vals in vals_list
            if vals.get("model")
        ]
        self._check_project_user_message_manage_access(candidates)
        return super().create(vals_list)

    def write(self, vals):
        candidates = []
        for message in self:
            candidates.append((vals.get("model", message.model), vals.get("res_id", message.res_id)))
        self._check_project_user_message_manage_access(candidates)
        return super().write(vals)

    def unlink(self):
        candidates = [(message.model, message.res_id) for message in self]
        self._check_project_user_message_manage_access(candidates)
        return super().unlink()


class MailActivity(models.Model):
    _inherit = "mail.activity"

    def _check_project_task_activity_access(self, vals_list):
        user = self.env.user
        if not user.has_group("project.group_project_user") or user.has_group(
            "project.group_project_manager"
        ):
            return
        for vals in vals_list:
            model = vals.get("res_model")
            if not model and vals.get("res_model_id"):
                model = self.env["ir.model"].sudo().browse(vals["res_model_id"]).model
            res_id = vals.get("res_id")
            if model != "project.task" or not res_id:
                continue
            if not self.env["project.task"]._is_user_task_manager_by_id(res_id, user):
                raise AccessError(
                    _(
                        "You can only schedule activities on tasks where you are the project responsible or an assignee."
                    )
                )

    @api.model_create_multi
    def create(self, vals_list):
        self._check_project_task_activity_access(vals_list)
        return super().create(vals_list)

    def write(self, vals):
        vals_list = []
        for activity in self:
            candidate_vals = dict(vals)
            candidate_vals.setdefault("res_model", activity.res_model)
            candidate_vals.setdefault("res_id", activity.res_id)
            vals_list.append(candidate_vals)
        self._check_project_task_activity_access(vals_list)
        return super().write(vals)


class IrAttachment(models.Model):
    _inherit = "ir.attachment"

    _PROJECT_GUARDED_MODELS = {
        "project.project",
        "project.task",
        "project.milestone",
        "project.update",
    }

    def _is_allowed_project_attachment_target(self, model_name, res_id, user):
        if model_name not in self._PROJECT_GUARDED_MODELS:
            return True
        if not res_id:
            return False
        record = self.env[model_name].sudo().browse(res_id).exists()
        if not record:
            return False
        if model_name == "project.project":
            return record.user_id == user
        if model_name == "project.task":
            return record.project_id.user_id == user or user in record.user_ids
        return record.project_id.user_id == user

    def _check_project_user_attachment_guard(self, vals_list):
        user = self.env.user
        if not user.has_group("project.group_project_user") or user.has_group(
            "project.group_project_manager"
        ):
            return

        for vals in vals_list:
            model_name = vals.get("res_model")
            res_id = vals.get("res_id")
            if not model_name or model_name not in self._PROJECT_GUARDED_MODELS:
                continue
            if not self._is_allowed_project_attachment_target(model_name, res_id, user):
                raise AccessError(
                    _(
                        "You can only manage attachments on project records where you are the project responsible or task assignee."
                    )
                )

    @api.model_create_multi
    def create(self, vals_list):
        self._check_project_user_attachment_guard(vals_list)
        return super().create(vals_list)

    def write(self, vals):
        user = self.env.user
        if user.has_group("project.group_project_user") and not user.has_group(
            "project.group_project_manager"
        ):
            for attachment in self:
                model_name = vals.get("res_model", attachment.res_model)
                res_id = vals.get("res_id", attachment.res_id)
                if model_name in self._PROJECT_GUARDED_MODELS and not self._is_allowed_project_attachment_target(
                    model_name, res_id, user
                ):
                    raise AccessError(
                        _(
                            "You can only manage attachments on project records where you are the project responsible or task assignee."
                        )
                    )
        return super().write(vals)

    def unlink(self):
        user = self.env.user
        if user.has_group("project.group_project_user") and not user.has_group(
            "project.group_project_manager"
        ):
            for attachment in self:
                model_name = attachment.res_model
                res_id = attachment.res_id
                if model_name in self._PROJECT_GUARDED_MODELS and not self._is_allowed_project_attachment_target(
                    model_name, res_id, user
                ):
                    raise AccessError(
                        _(
                            "You can only manage attachments on project records where you are the project responsible or task assignee."
                        )
                    )
        return super().unlink()
