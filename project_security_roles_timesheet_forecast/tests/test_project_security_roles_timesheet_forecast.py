from odoo import Command, fields
from odoo.tests.common import TransactionCase


class TestProjectSecurityRolesTimesheetForecast(TransactionCase):
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
                "name": "TS Forecast Project User Owner",
                "login": "ts_forecast_project_user_owner",
                "groups_id": [Command.set([cls.group_project_user.id, cls.group_hr_timesheet_user.id])],
            }
        )
        cls.user_peer = cls.env["res.users"].create(
            {
                "name": "TS Forecast Project User Peer",
                "login": "ts_forecast_project_user_peer",
                "groups_id": [Command.set([cls.group_project_user.id, cls.group_hr_timesheet_user.id])],
            }
        )

        cls.employee_owner = cls.env["hr.employee"].create(
            {
                "name": "TS Forecast Employee Owner",
                "user_id": cls.user_owner.id,
                "company_id": cls.env.company.id,
            }
        )
        cls.employee_peer = cls.env["hr.employee"].create(
            {
                "name": "TS Forecast Employee Peer",
                "user_id": cls.user_peer.id,
                "company_id": cls.env.company.id,
            }
        )

        cls.project_owner = cls.env["project.project"].sudo().create(
            {
                "name": "TS Forecast Project Owner",
                "user_id": cls.user_owner.id,
                "privacy_visibility": "followers",
            }
        )
        cls.project_follower = cls.env["project.project"].sudo().create(
            {
                "name": "TS Forecast Project Follower",
                "user_id": cls.user_peer.id,
                "privacy_visibility": "followers",
            }
        )
        cls.project_team = cls.env["project.project"].sudo().create(
            {
                "name": "TS Forecast Project Team",
                "user_id": cls.user_peer.id,
                "privacy_visibility": "portal",
            }
        )
        cls.project_hidden = cls.env["project.project"].sudo().create(
            {
                "name": "TS Forecast Project Hidden",
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
        line_model = cls.env["account.analytic.line"].sudo()
        line_model.create(
            {
                "name": "TS Forecast Owner Line",
                "project_id": cls.project_owner.id,
                "employee_id": cls.employee_owner.id,
                "user_id": cls.user_owner.id,
                "unit_amount": 1.0,
                "date": today,
            }
        )
        line_model.create(
            {
                "name": "TS Forecast Follower Line",
                "project_id": cls.project_follower.id,
                "employee_id": cls.employee_peer.id,
                "user_id": cls.user_peer.id,
                "unit_amount": 1.0,
                "date": today,
            }
        )
        line_model.create(
            {
                "name": "TS Forecast Team Line",
                "project_id": cls.project_team.id,
                "employee_id": cls.employee_peer.id,
                "user_id": cls.user_peer.id,
                "unit_amount": 1.0,
                "date": today,
            }
        )
        line_model.create(
            {
                "name": "TS Forecast Hidden Line",
                "project_id": cls.project_hidden.id,
                "employee_id": cls.employee_peer.id,
                "user_id": cls.user_peer.id,
                "unit_amount": 1.0,
                "date": today,
            }
        )

    def test_forecast_report_visibility_is_limited_to_owner_follower_team(self):
        report_lines = self.env["project.timesheet.forecast.report.analysis"].with_user(
            self.user_owner
        ).search(
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
                ),
                ("line_type", "=", "timesheet"),
            ]
        )
        project_ids = set(report_lines.mapped("project_id").ids)
        self.assertIn(self.project_owner.id, project_ids)
        self.assertIn(self.project_follower.id, project_ids)
        self.assertIn(self.project_team.id, project_ids)
        self.assertNotIn(self.project_hidden.id, project_ids)
