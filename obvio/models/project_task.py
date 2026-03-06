from odoo import api, fields, models, _

class ProjecTask(models.Model):
    _inherit = 'project.task'

    name = fields.Char(translate=True)

    is_subtask_seq = fields.Boolean(string='Is a Sub-task', default=False)
    parent_task_seq_id = fields.Many2one('project.task', string='Parent Task', domain="[('project_id', '=', project_id)]")
    subtask_seq_suffix = fields.Char(string='Sub-task Suffix', size=2)
    sequence_new = fields.Char(string='Sequence', readonly=True, copy=False)

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('is_subtask_seq') and vals.get('parent_task_seq_id'):
                parent = self.env['project.task'].browse(vals['parent_task_seq_id'])
                suffix = vals.get('subtask_seq_suffix', '').strip()
                if parent.sequence_new:
                    base_sequence = parent.sequence_new
                    if base_sequence.split(' ')[-1].isalpha() and len(base_sequence.split(' ')[-1]) <= 2:
                        base_sequence = ' '.join(base_sequence.split(' ')[:-1])
                    vals['sequence_new'] = f"{base_sequence} {suffix}" if suffix else base_sequence
                else:
                    vals['sequence_new'] = self.env['ir.sequence'].next_by_code('project.task') or '/'
                    if suffix:
                        vals['sequence_new'] = f"{vals['sequence_new']} {suffix}"
            else:
                if not vals.get('sequence_new') or vals['sequence_new'] in ['New', '/', False]:
                    vals['sequence_new'] = self.env['ir.sequence'].next_by_code('project.task') or '/'

        return super(ProjecTask, self).create(vals_list)

    def write(self, vals):
        res = super(ProjecTask, self).write(vals)

        campos_nomenclatura = [
            'is_subtask_seq',
            'parent_task_seq_id',
            'subtask_seq_suffix',
        ]

        if any(campo in vals for campo in campos_nomenclatura):
            for task in self:
                is_subtask_seq = vals.get('is_subtask_seq', task.is_subtask_seq)
                if is_subtask_seq:
                    parent_task_seq_id = vals.get('parent_task_seq_id', task.parent_task_seq_id.id)
                    subtask_seq_suffix = vals.get('subtask_seq_suffix', task.subtask_seq_suffix or '').strip()
                    if parent_task_seq_id:
                        parent = self.env['project.task'].browse(parent_task_seq_id)
                        if parent.sequence_new:
                            base_sequence = parent.sequence_new
                            if base_sequence.split(' ')[-1].isalpha() and len(base_sequence.split(' ')[-1]) <= 2:
                                base_sequence = ' '.join(base_sequence.split(' ')[:-1])
                            sequence_new = f"{base_sequence} {subtask_seq_suffix}" if subtask_seq_suffix else base_sequence
                            if task.sequence_new != sequence_new:
                                super(ProjecTask, task).write({'sequence_new': sequence_new})

        return res