from odoo import api, fields, models, _


class EquipmentType(models.Model):
    _name = 'equipment.type'
    _description = 'Equipment type'
    _rec_name = 'alias_name'

    name = fields.Char(string='Name', required=True)
    alias_name = fields.Char(string='Alias', required=True)
    user_id = fields.Many2one('res.users', string='Responsible')
    company_id = fields.Many2one(
        'res.company',
        string='Company',
        default=lambda self: self.env.company,
        required=True,
        index=True
    )
    note = fields.Html(string='Comment')


  


