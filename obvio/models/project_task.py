from odoo import api, fields, models, _

class ProjecTask(models.Model):
    _inherit = 'project.task'

    name = fields.Char(translate=True)