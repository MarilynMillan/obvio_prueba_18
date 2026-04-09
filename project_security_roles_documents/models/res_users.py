from odoo import Command, fields, models


class ResUsers(models.Model):
    _inherit = "res.users"

    project_security_visible_project_ids = fields.Many2many(
        "project.project",
        compute="_compute_project_security_visible_project_ids",
        export_string_translation=False,
    )

    def _compute_project_security_visible_project_ids(self):
        projects_model = self.env["project.project"].sudo()
        for user in self:
            partner = user.partner_id
            domain = [
                "|",
                "|",
                ("user_id", "=", user.id),
                ("message_partner_ids", "in", [partner.id]),
                ("collaborator_ids.partner_id", "=", partner.id),
            ]
            projects = projects_model.search(domain)
            user.project_security_visible_project_ids = [Command.set(projects.ids)]
