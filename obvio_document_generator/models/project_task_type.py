from odoo import models, fields

class ProjectTaskType(models.Model):
    _inherit = 'project.task.type'

    is_document_generator = fields.Boolean(
        string="Generate Document",
        help="If checked, tasks in this stage will be able to generate documents.",
        default=False
    )
