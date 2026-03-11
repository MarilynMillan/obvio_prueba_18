{
    'name': 'Obvio Document Generator',
    'version': '18.0.1.0.0',
    'category': 'Project',
    'summary': 'Generate automatic documents from project tasks based on stage configuration.',
    'description': """
        This module allows users to generate a document from a project task.
        - Adds configuration on Task Stages to allow document generation.
        - In the Task, if the stage allows it, a "Generate Document" button is shown.
        - Generates a PDF containing project details (from obvio module) and task images/comments.
    """,
    'author': 'Your Name',
    'depends': ['project', 'obvio'],
    'data': [
        'views/project_task_type_views.xml',
        'views/project_task_views.xml',
        'report/document_report.xml',
        'report/document_report_templates.xml',
    ],
    'installable': True,
    'application': False,
    'license': 'LGPL-3',
}
