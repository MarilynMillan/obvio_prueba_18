{
    "name": "Project Security Roles Forecast",
    "version": "18.0.1.0.0",
    "summary": "Restrict project forecast management for Project/User",
    "category": "Services/Project",
    "author": "Navegasoft",
    "license": "OPL-1",
    "depends": ["project_security_roles", "project_forecast"],
    "data": [
        "security/ir.model.access.csv",
        "security/project_security_roles_forecast_rules.xml",
        "views_planning_send.xml",
    ],
    "installable": True,
    "auto_install": True,
}
