from odoo import api, fields, models, _

class ProjecTask(models.Model):
    _inherit = 'project.task'

    name = fields.Char(translate=True)

    def write(self, vals):
        # Evitar que las tareas canceladas se archiven (active=False) en Odoo 18
        if 'active' in vals and not vals['active']:
            state_val = vals.get('state')
            if state_val == '1_canceled':
                vals.pop('active')
                return super(ProjecTask, self).write(vals)

            tasks_canceled = self.filtered(lambda t: t.state == '1_canceled')
            tasks_others = self - tasks_canceled

            if tasks_canceled:
                vals_for_canceled = vals.copy()
                vals_for_canceled.pop('active')

                res = True
                if vals_for_canceled:
                    res = super(ProjecTask, tasks_canceled).write(vals_for_canceled)
                if tasks_others:
                    res = res and super(ProjecTask, tasks_others).write(vals)
                return res

        return super(ProjecTask, self).write(vals)