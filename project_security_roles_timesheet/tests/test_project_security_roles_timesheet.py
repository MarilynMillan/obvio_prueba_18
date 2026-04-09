from odoo import Command, fields
from odoo.exceptions import AccessError
from odoo.tests.common import TransactionCase


class TestProjectSecurityRolesTimesheet(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(
            context=dict(cls.env.context, tracking_disable=True, no_reset_password=True)
        )
        cls.group_project_user = cls.env.ref("project.group_project_user")
        cls.group_hr_timesheet_user = cls.env.ref("hr_timesheet.group_hr_timesheet_user")

        cls.user_owner = cls.env["res.users"].create(
            {
                "name": "Timesheet Project User Owner",
                "login": "timesheet_project_user_owner",
                "groups_id": [Command.set([cls.group_project_user.id, cls.group_hr_timesheet_user.id])],
            }
        )
        cls.user_peer = cls.env["res.users"].create(
            {
                "name": "Timesheet Project User Peer",
                "login": "timesheet_project_user_peer",
                "groups_id": [Command.set([cls.group_project_user.id, cls.group_hr_timesheet_user.id])],
            }
        )

        cls.employee_owner = cls.env["hr.employee"].create(
            {
                "name": "Timesheet Employee Owner",
                "user_id": cls.user_owner.id,
                "company_id": cls.env.company.id,
            }
        )
        cls.employee_peer = cls.env["hr.employee"].create(
            {
                "name": "Timesheet Employee Peer",
                "user_id": cls.user_peer.id,
                "company_id": cls.env.company.id,
            }
        )

        cls.project_owner = cls.env["project.project"].sudo().create(
            {
                "name": "Timesheet Project Owner",
                "user_id": cls.user_owner.id,
                "privacy_visibility": "followers",
            }
        )
        cls.project_follower = cls.env["project.project"].sudo().create(
            {
                "name": "Timesheet Project Follower",
                "user_id": cls.user_peer.id,
                "privacy_visibility": "followers",
            }
        )
        cls.project_team = cls.env["project.project"].sudo().create(
            {
                "name": "Timesheet Project Team",
                "user_id": cls.user_peer.id,
                "privacy_visibility": "portal",
            }
        )
        cls.project_hidden = cls.env["project.project"].sudo().create(
            {
                "name": "Timesheet Project Hidden",
                "user_id": cls.user_peer.id,
                "privacy_visibility": "followers",
            }
        )

        cls.project_follower.sudo().message_subscribe(partner_ids=cls.user_owner.partner_id.ids)
        cls.env["project.collaborator"].sudo().create(
            {
                "project_id": cls.project_team.id,
                "partner_id": cls.user_owner.partner_id.id,
            }
        )

        today = fields.Date.today()
        cls.line_owner = cls.env["account.analytic.line"].sudo().create(
            {
                "name": "Line Owner",
                "project_id": cls.project_owner.id,
                "employee_id": cls.employee_owner.id,
                "user_id": cls.user_owner.id,
                "unit_amount": 1.0,
                "date": today,
            }
        )
        cls.line_follower = cls.env["account.analytic.line"].sudo().create(
            {
                "name": "Line Follower",
                "project_id": cls.project_follower.id,
                "employee_id": cls.employee_peer.id,
                "user_id": cls.user_peer.id,
                "unit_amount": 1.0,
                "date": today,
            }
        )
        cls.line_team = cls.env["account.analytic.line"].sudo().create(
            {
                "name": "Line Team",
                "project_id": cls.project_team.id,
                "employee_id": cls.employee_peer.id,
                "user_id": cls.user_peer.id,
                "unit_amount": 1.0,
                "date": today,
            }
        )
        cls.line_hidden = cls.env["account.analytic.line"].sudo().create(
            {
                "name": "Line Hidden",
                "project_id": cls.project_hidden.id,
                "employee_id": cls.employee_peer.id,
                "user_id": cls.user_peer.id,
                "unit_amount": 1.0,
                "date": today,
            }
        )

    def test_timesheet_visibility_is_limited_to_owner_follower_team(self):
        lines = self.env["account.analytic.line"].with_user(self.user_owner).search(
            [("id", "in", [self.line_owner.id, self.line_follower.id, self.line_team.id, self.line_hidden.id])]
        )
        self.assertIn(self.line_owner, lines)
        self.assertIn(self.line_follower, lines)
        self.assertIn(self.line_team, lines)
        self.assertNotIn(self.line_hidden, lines)

    def test_project_user_can_manage_only_owned_project_timesheets(self):
        today = fields.Date.today()
        self.env["account.analytic.line"].with_user(self.user_owner).create(
            {
                "name": "Own Managed Line",
                "project_id": self.project_owner.id,
                "employee_id": self.employee_owner.id,
                "user_id": self.user_owner.id,
                "unit_amount": 2.0,
                "date": today,
            }
        )

        with self.assertRaises(AccessError):
            self.env["account.analytic.line"].with_user(self.user_owner).create(
                {
                    "name": "Follower Managed Line Blocked",
                    "project_id": self.project_follower.id,
                    "employee_id": self.employee_owner.id,
                    "user_id": self.user_owner.id,
                    "unit_amount": 1.0,
                    "date": today,
                }
            )

        self.line_owner.with_user(self.user_owner).write({"name": "Owner Edited"})
        with self.assertRaises(AccessError):
            self.line_follower.with_user(self.user_owner).write({"name": "Follower Edit Blocked"})

    def test_timesheet_report_visibility_is_limited_to_owner_follower_team(self):
        report_lines = self.env["timesheets.analysis.report"].with_user(self.user_owner).search(
            [
                (
                    "project_id",
                    "in",
                    [
                        self.project_owner.id,
                        self.project_follower.id,
                        self.project_team.id,
                        self.project_hidden.id,
                    ],
                )
            ]
        )
        project_ids = set(report_lines.mapped("project_id").ids)
        self.assertIn(self.project_owner.id, project_ids)
        self.assertIn(self.project_follower.id, project_ids)
        self.assertIn(self.project_team.id, project_ids)
        self.assertNotIn(self.project_hidden.id, project_ids)
