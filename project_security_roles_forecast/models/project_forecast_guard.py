from odoo import _, api, models
from odoo.exceptions import AccessError


class PlanningSlot(models.Model):
    _inherit = "planning.slot"

    def _is_project_user_restricted(self):
        user = self.env.user
        return user.has_group("project.group_project_user") and not user.has_group(
            "project.group_project_manager"
        )

    def _is_allowed_slot_target(self, project_id, slot_user_id, user):
        project = (
            self.env["project.project"].sudo().browse(project_id).exists()
            if project_id
            else self.env["project.project"]
        )

        if not project:
            return False

        if project and project.user_id == user:
            return True
        return False

    def _check_project_user_planning_guard(self, vals_list=None, records=None):
        if not self._is_project_user_restricted():
            return

        user = self.env.user
        if vals_list:
            for vals in vals_list:
                project_id = vals.get("project_id")
                slot_user_id = vals.get("user_id")
                if project_id is False:
                    project_id = None
                if slot_user_id is False:
                    slot_user_id = None
                if not self._is_allowed_slot_target(project_id, slot_user_id, user):
                    raise AccessError(
                        _(
                            "You can only manage forecast shifts on projects where you are the responsible or shifts assigned to you."
                        )
                    )

        if records:
            for slot in records:
                if not self._is_allowed_slot_target(slot.project_id.id, slot.user_id.id, user):
                    raise AccessError(
                        _(
                            "You can only manage forecast shifts on projects where you are the responsible or shifts assigned to you."
                        )
                    )

    @api.model_create_multi
    def create(self, vals_list):
        self._check_project_user_planning_guard(vals_list=vals_list)
        return super().create(vals_list)

    def write(self, vals):
        if self._is_project_user_restricted():
            user = self.env.user
            for slot in self:
                project_id = vals.get("project_id", slot.project_id.id)
                slot_user_id = vals.get("user_id", slot.user_id.id)
                if project_id is False:
                    project_id = None
                if slot_user_id is False:
                    slot_user_id = None
                if not self._is_allowed_slot_target(project_id, slot_user_id, user):
                    raise AccessError(
                        _(
                            "You can only manage forecast shifts on projects where you are the responsible or shifts assigned to you."
                        )
                    )
        return super().write(vals)

    def unlink(self):
        self._check_project_user_planning_guard(records=self)
        return super().unlink()


class PlanningSlotTemplate(models.Model):
    _inherit = "planning.slot.template"

    def _is_project_user_restricted(self):
        user = self.env.user
        return user.has_group("project.group_project_user") and not user.has_group(
            "project.group_project_manager"
        )

    def _is_allowed_project_target(self, project_id, user):
        if not project_id:
            return False
        project = self.env["project.project"].sudo().browse(project_id).exists()
        return bool(project) and project.user_id == user

    def _check_project_user_template_guard(self, vals_list=None, records=None):
        if not self._is_project_user_restricted():
            return

        user = self.env.user
        if vals_list:
            for vals in vals_list:
                project_id = vals.get("project_id")
                if project_id is False:
                    project_id = None
                if not self._is_allowed_project_target(project_id, user):
                    raise AccessError(
                        _(
                            "You can only manage forecast templates on projects where you are the responsible."
                        )
                    )

        if records:
            for template in records:
                if not self._is_allowed_project_target(template.project_id.id, user):
                    raise AccessError(
                        _(
                            "You can only manage forecast templates on projects where you are the responsible."
                        )
                    )

    @api.model_create_multi
    def create(self, vals_list):
        self._check_project_user_template_guard(vals_list=vals_list)
        return super().create(vals_list)

    def write(self, vals):
        if self._is_project_user_restricted():
            user = self.env.user
            for template in self:
                project_id = vals.get("project_id", template.project_id.id)
                if project_id is False:
                    project_id = None
                if not self._is_allowed_project_target(project_id, user):
                    raise AccessError(
                        _(
                            "You can only manage forecast templates on projects where you are the responsible."
                        )
                    )
        return super().write(vals)

    def unlink(self):
        self._check_project_user_template_guard(records=self)
        return super().unlink()
