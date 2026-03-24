# -*- coding: utf-8 -*-
{
    'name': 'Obvio Tracking',
    'version': '1.0',
    'category': 'Project',
    'summary': 'Add tracking for Log Notes and Tasks',
    'description': """
        This module adds traceability for:
        - Edition and deletion of Log Notes.
        - Track canceled tasks.
        - Track assignment of tasks when marked as done.
    """,
    'depends': ['project', 'mail', 'obvio'],
    'data': [
        'views/project_task_views.xml',
    ],
    'installable': True,
    'application': False,
    'license': 'LGPL-3',
}
