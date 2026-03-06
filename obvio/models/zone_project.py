from odoo import api, fields, models, _

class ProjectZone(models.Model):
    _name = 'project.zone'
    _description = 'Project country'
    _rec_name = 'display_name' 

  
    zone_ubication_ids = fields.One2many('zone.ubication', 'zone_id', string='Location')
    country_id = fields.Many2one('res.country', string= 'Country')
    code = fields.Char( string='ISO code',size=3)
    display_name = fields.Char(compute='_compute_display_name', store=True, translate=True)


    @api.depends('country_id')
    def _compute_display_name(self):
        for record in self:
            if record.country_id:
                record.display_name = record.country_id.name
            else:
                record.display_name = ''


class ZoneUbicaction(models.Model):
    _name = 'zone.ubication'
    _description = 'Project location'
    _rec_name = 'zone'

    name = fields.Char(string='Name' )
    zone = fields.Char(string='Code' )
    zone_id = fields.Many2one('project.zone', string='Country', required=True)
    zone_tienda_ids = fields.One2many('zone.tienda', 'ubication_id', string='Stores')




class ZoneTienda(models.Model):
    _name = 'zone.tienda'
    _description = 'Project store'
    _rec_name = 'tienda'

    name = fields.Char(string='Name' )
    tienda = fields.Char(string='Code' )
    ubication_id = fields.Many2one('zone.ubication', string='Location', required=True)


