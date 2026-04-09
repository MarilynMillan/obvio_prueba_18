{
    "name": "Project Security Roles",
    "version": "18.0.1.0.0",
    "summary": "Project user ownership-based security rules",
    "category": "Services/Project",
    "author": "Navegasoft",
    "license": "OPL-1",
    "depends": ["project", "project_enterprise", "mail"],
    "data": [
        "security/ir.model.access.csv",
        "security/project_security_roles_rules.xml",
        "views/project_task_views.xml",
    ],
    "assets": {
        "web.assets_backend": [
            "project_security_roles/static/src/js/project_task_kanban_renderer_patch.js",
        ],
    },
    "installable": True,
}
