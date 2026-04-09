import base64

from odoo import Command
from odoo.exceptions import AccessError, UserError
from odoo.tests.common import TransactionCase


class TestProjectSecurityRoles(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(
            context=dict(cls.env.context, tracking_disable=True, no_reset_password=True)
        )
        cls.group_project_user = cls.env.ref("project.group_project_user")
        cls.group_project_admin = cls.env.ref("project.group_project_manager")

        cls.user_a = cls.env["res.users"].create(
            {
                "name": "Project User A",
                "login": "project_user_a_security_roles",
                "groups_id": [Command.set([cls.group_project_user.id])],
            }
        )
        cls.user_b = cls.env["res.users"].create(
            {
                "name": "Project User B",
                "login": "project_user_b_security_roles",
                "groups_id": [Command.set([cls.group_project_user.id])],
            }
        )
        cls.user_admin = cls.env["res.users"].create(
            {
                "name": "Project Administrator",
                "login": "project_admin_security_roles",
                "groups_id": [Command.set([cls.group_project_admin.id])],
            }
        )

        cls.project_a = cls.env["project.project"].sudo().create(
            {"name": "Project A", "user_id": cls.user_a.id, "privacy_visibility": "followers"}
        )
        cls.project_b_follower = cls.env["project.project"].sudo().create(
            {"name": "Project B Follower", "user_id": cls.user_b.id, "privacy_visibility": "followers"}
        )
        cls.project_b_team = cls.env["project.project"].sudo().create(
            {"name": "Project B Team", "user_id": cls.user_b.id, "privacy_visibility": "portal"}
        )
        cls.project_b_hidden = cls.env["project.project"].sudo().create(
            {"name": "Project B Hidden", "user_id": cls.user_b.id, "privacy_visibility": "followers"}
        )

        cls.project_b_follower.sudo().message_subscribe(partner_ids=cls.user_a.partner_id.ids)
        cls.env["project.collaborator"].sudo().create(
            {
                "project_id": cls.project_b_team.id,
                "partner_id": cls.user_a.partner_id.id,
            }
        )
        cls.task_a = cls.env["project.task"].sudo().create(
            {"name": "Task A", "project_id": cls.project_a.id}
        )
        cls.task_b_follower = cls.env["project.task"].sudo().create(
            {"name": "Task B Follower", "project_id": cls.project_b_follower.id}
        )
        cls.task_b_team = cls.env["project.task"].sudo().create(
            {"name": "Task B Team", "project_id": cls.project_b_team.id}
        )
        cls.task_b_hidden = cls.env["project.task"].sudo().create(
            {"name": "Task B Hidden", "project_id": cls.project_b_hidden.id}
        )
        cls.task_b_assigned = cls.env["project.task"].sudo().create(
            {
                "name": "Task B Assigned",
                "project_id": cls.project_b_hidden.id,
                "user_ids": [Command.set([cls.user_a.id])],
            }
        )
        cls.milestone_a = cls.env["project.milestone"].sudo().create(
            {"name": "Milestone A", "project_id": cls.project_a.id}
        )
        cls.activity_type_todo = cls.env.ref("mail.mail_activity_data_todo")

    def test_visibility_rules(self):
        projects = self.env["project.project"].with_user(self.user_a).search([])
        self.assertIn(self.project_a, projects)
        self.assertIn(self.project_b_follower, projects)
        self.assertIn(self.project_b_team, projects)
        self.assertNotIn(self.project_b_hidden, projects)

    def test_own_projects_edit(self):
        self.project_a.with_user(self.user_a).write({"name": "A updated"})
        with self.assertRaises(AccessError):
            self.project_b_hidden.with_user(self.user_a).write({"name": "Blocked"})

    def test_create_is_limited_to_own_manager(self):
        self.env["project.project"].with_user(self.user_a).create({"name": "A created"})
        with self.assertRaises(AccessError):
            self.env["project.project"].with_user(self.user_a).create(
                {"name": "Wrong owner", "user_id": self.user_b.id}
            )

    def test_project_admin_still_has_full_access(self):
        self.project_b_hidden.with_user(self.user_admin).write({"name": "Admin edit"})

    def test_tasks_allow_own_project_and_block_third_party(self):
        self.task_a.with_user(self.user_a).write({"name": "Own task edit"})
        self.task_b_assigned.with_user(self.user_a).write({"name": "Assigned task edit"})
        self.env["project.task"].with_user(self.user_a).create(
            {"name": "Own task create", "project_id": self.project_a.id}
        )
        with self.assertRaises(AccessError):
            self.env["project.task"].with_user(self.user_a).create(
                {"name": "Blocked task create", "project_id": self.project_b_hidden.id}
            )

    def test_private_tasks_can_be_created_but_cannot_be_moved_to_foreign_project(self):
        private_task = self.env["project.task"].with_user(self.user_a).create(
            {
                "name": "Private todo",
                "project_id": False,
                "user_ids": [Command.set([self.user_a.id])],
            }
        )
        self.assertFalse(private_task.project_id)

        with self.assertRaises(AccessError):
            private_task.with_user(self.user_a).write({"project_id": self.project_b_hidden.id})

        private_task.with_user(self.user_a).write({"project_id": self.project_a.id})
        self.assertEqual(private_task.project_id, self.project_a)

    def test_task_visibility_is_limited_to_own_follower_or_team(self):
        tasks = self.env["project.task"].with_user(self.user_a).search([])
        self.assertIn(self.task_a, tasks)
        self.assertIn(self.task_b_assigned, tasks)
        self.assertNotIn(self.task_b_follower, tasks)
        self.assertNotIn(self.task_b_team, tasks)
        self.assertNotIn(self.task_b_hidden, tasks)

    def test_task_report_visibility_is_limited_to_own_follower_or_team(self):
        report_lines = self.env["report.project.task.user"].with_user(self.user_a).search(
            [
                (
                    "task_id",
                    "in",
                    [
                        self.task_a.id,
                        self.task_b_assigned.id,
                        self.task_b_follower.id,
                        self.task_b_team.id,
                        self.task_b_hidden.id,
                    ],
                )
            ]
        )
        task_ids = report_lines.mapped("task_id").ids
        self.assertIn(self.task_a.id, task_ids)
        self.assertIn(self.task_b_assigned.id, task_ids)
        self.assertNotIn(self.task_b_follower.id, task_ids)
        self.assertNotIn(self.task_b_team.id, task_ids)
        self.assertNotIn(self.task_b_hidden.id, task_ids)

    def test_milestones_security_configuration(self):
        own_milestone_rule = self.env.ref("project_security_roles.rule_milestone_user_own_edit")
        self.assertTrue(own_milestone_rule.perm_write)
        self.assertTrue(own_milestone_rule.perm_create)
        self.assertEqual(own_milestone_rule.domain_force, "[('project_id.user_id', '=', user.id)]")

        milestone_acl = self.env["ir.model.access"].search(
            [
                ("name", "=", "project.milestone user owned"),
                ("group_id", "=", self.group_project_user.id),
                ("model_id.model", "=", "project.milestone"),
            ],
            limit=1,
        )
        self.assertTrue(milestone_acl)
        self.assertTrue(milestone_acl.perm_write)
        self.assertTrue(milestone_acl.perm_create)

    def test_project_updates_allow_own_project_and_block_third_party(self):
        self.env["project.update"].with_user(self.user_a).create(
            {
                "name": "Own update",
                "status": "on_track",
                "project_id": self.project_a.id,
            }
        )
        with self.assertRaises(AccessError):
            self.env["project.update"].with_user(self.user_a).create(
                {
                    "name": "Blocked update",
                    "status": "at_risk",
                    "project_id": self.project_b_hidden.id,
                }
            )

    def test_import_is_blocked_for_project_user(self):
        with self.assertRaises(UserError):
            self.env["project.task"].with_user(self.user_a).load(
                ["name", "project_id/id"],
                [["Imported by file", str(self.project_a.id)]],
            )

    def test_alias_name_edit_is_limited_to_own_project(self):
        self.project_a.with_user(self.user_a).write({"alias_name": "own-alias-a"})
        with self.assertRaises(AccessError):
            self.project_b_follower.with_user(self.user_a).write(
                {"alias_name": "blocked-alias-b"}
            )

    def test_task_activity_scheduling_is_limited_to_own_project(self):
        self.task_a.with_user(self.user_a).activity_schedule(
            act_type_xmlid="mail.mail_activity_data_todo",
            summary="Own task activity",
        )
        self.task_b_assigned.with_user(self.user_a).activity_schedule(
            act_type_xmlid="mail.mail_activity_data_todo",
            summary="Assigned task activity",
        )
        with self.assertRaises(AccessError):
            self.task_b_hidden.with_user(self.user_a).activity_schedule(
                act_type_xmlid="mail.mail_activity_data_todo",
                summary="Blocked third-party activity",
            )

    def test_attachment_upload_is_limited_to_own_project_records(self):
        self.env["ir.attachment"].with_user(self.user_a).create(
            {
                "name": "own-task.txt",
                "type": "binary",
                "datas": base64.b64encode(b"ok"),
                "mimetype": "text/plain",
                "res_model": "project.task",
                "res_id": self.task_a.id,
            }
        )
        self.env["ir.attachment"].with_user(self.user_a).create(
            {
                "name": "assigned-task.txt",
                "type": "binary",
                "datas": base64.b64encode(b"assigned"),
                "mimetype": "text/plain",
                "res_model": "project.task",
                "res_id": self.task_b_assigned.id,
            }
        )
        with self.assertRaises(AccessError):
            self.env["ir.attachment"].with_user(self.user_a).create(
                {
                    "name": "other-task.txt",
                    "type": "binary",
                    "datas": base64.b64encode(b"blocked"),
                    "mimetype": "text/plain",
                    "res_model": "project.task",
                    "res_id": self.task_b_follower.id,
                }
            )

    def test_task_stage_creation_is_limited_to_owned_projects(self):
        self.env["project.task.type"].with_user(self.user_a).create(
            {
                "name": "Own Project Stage",
                "project_ids": [Command.set([self.project_a.id])],
            }
        )
        self.env["project.task.type"].with_user(self.user_a).create(
            {
                "name": "Own Personal Stage",
                "user_id": self.user_a.id,
            }
        )
        with self.assertRaises(AccessError):
            self.env["project.task.type"].with_user(self.user_a).create(
                {
                    "name": "Global Stage Blocked",
                }
            )
        with self.assertRaises(AccessError):
            self.env["project.task.type"].with_user(self.user_a).create(
                {
                    "name": "Foreign Personal Stage",
                    "user_id": self.user_b.id,
                }
            )
        with self.assertRaises(AccessError):
            self.env["project.task.type"].with_user(self.user_a).create(
                {
                    "name": "Foreign Project Stage",
                    "project_ids": [Command.set([self.project_b_hidden.id])],
                }
            )
        self.env["project.task.type"].with_context(default_project_ids=[self.project_a.id]).with_user(
            self.user_a
        ).create({"name": "Own Stage From Context"})
        with self.assertRaises(AccessError):
            self.env["project.task.type"].with_context(
                default_project_ids=[self.project_b_hidden.id]
            ).with_user(self.user_a).create({"name": "Foreign Stage From Context"})
        with self.assertRaises(AccessError):
            self.env["project.task.type"].with_context(
                default_project_ids=False
            ).with_user(self.user_a).create({"name": "Invalid Context Stage"})
