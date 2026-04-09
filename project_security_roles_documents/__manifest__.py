{
    "name": "Project Security Roles Documents",
    "version": "18.0.1.0.0",
    "summary": "Restrict project document management for Project/User",
    "category": "Services/Project",
    "author": "Navegasoft",
    "license": "OPL-1",
    "depends": ["project_security_roles", "documents_project"],
    "data": [
        "security/ir.model.access.csv",
        "security/project_security_roles_documents_rules.xml",
    ],
    "installable": True,
    "auto_install": True,
}
