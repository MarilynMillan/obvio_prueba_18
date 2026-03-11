from odoo import models, fields, api, _

class ProjectTask(models.Model):
    _inherit = 'project.task'

    document_comment = fields.Text(string="Document Comment", help="Comment to include in the generated document.")
    is_document_generator_stage = fields.Boolean(
        related='stage_id.is_document_generator',
        string="Is Document Generator Stage",
        readonly=True
    )

    def action_generate_document(self):
        """ Generates a PDF document for this task. """
        self.ensure_one()

        # Trigger report generation
        # 'obvio_document_generator.action_report_task_document' should be the xml id of the report
        report_action = self.env.ref('obvio_document_generator.action_report_task_document').report_action(self)
        return report_action

    def _get_document_images(self):
        """ Fetch images from the task attachments to include in the document. """
        self.ensure_one()
        attachments = self.env['ir.attachment'].search([
            ('res_model', '=', 'project.task'),
            ('res_id', '=', self.id),
            ('mimetype', 'ilike', 'image/')
        ], order='create_date asc')
        return attachments
