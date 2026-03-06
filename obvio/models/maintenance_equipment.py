from babel import Locale, UnknownLocaleError
from odoo import api, fields, models, _
from pytz import all_timezones, timezone
from datetime import datetime

class MaintenanceEquipment(models.Model):
    _inherit = 'maintenance.equipment'


    def _get_timezones_with_offsets(self):
        """Devuelve las zonas horarias junto con el UTC offset y el país."""
        current_time = datetime.now()  # Obtener el tiempo actual
        timezones = []
        for tz in all_timezones:
            tz_obj = timezone(tz)
            utc_offset = current_time.astimezone(tz_obj).strftime('%z')
            formatted_offset = f"(UTC {utc_offset[:3]}:{utc_offset[3:]})"

            # Extraer país y nombre de zona horaria
            country_name = self._get_country_name_from_timezone(tz)
            display_name = f"{country_name} / {tz} {formatted_offset}" if country_name else f"{tz} {formatted_offset}"
            
            timezones.append((tz, display_name))
        return timezones

    def _get_country_name_from_timezone(self, tz):
        """Devuelve el nombre del país basado en la zona horaria, si es posible."""
        try:
            # Obtener el país o localidad de la zona horaria
            region = tz.split('/')[-1].replace('_', ' ')
            locale = Locale.parse(region, sep='-')
            country_name = locale.get_display_name()
            return country_name
        except (UnknownLocaleError, ValueError):
            # Si no se puede determinar, devolver None
            return None

    name_equipment = fields.Char('Nombre Equipo')
    type_equipment = fields.Many2one('equipment.type', string= 'Equipment type')
    show_dss_tab = fields.Boolean(string='Mostrar Pestaña DSS', compute='_compute_show_dss_tab')
    project_sequence = fields.Char(string='Proyecto Asociado', readonly=True)
    time_zome = fields.Selection(
        selection=lambda self: self._get_timezones_with_offsets(),
        string="Zona Horaria",
        help="Selecciona la zona horaria de la localización"
    )
    make_time = fields.Char(string='Wake up time')
    sleeping_time = fields.Char(string='Sleeping Time')
    set_service = fields.Boolean(string='Set on Device')
    imagen_avatar = fields.Binary(string='imagen')
    contact_person = fields.Many2one('res.partner', string='Contact Person')
    product_service = fields.Many2one('product.product', string='Product Service')
    other_service = fields.Many2one('product.product', string='Other Services')
    project_id = fields.Many2one('project.project', string='Proyecto Asociado')
    image_ids = fields.One2many('maintenance.equipment.image', 'equipment_id',string="Registro")
    technical_image_ids = fields.One2many('maintenance.equipment.image.technical', 'technical_id',string="Registro")
    hardware_image_ids = fields.One2many('maintenance.equipment.image.hardware', 'hardware_id',string="Registro")

    providenci_1 = fields.Many2one('res.partner', string='Provider 1')
    user_id_1 = fields.Char(string='User')
    passwords_1 = fields.Char(string='Pass')
    optional = fields.Boolean(string='Optional')
    providenci_2 = fields.Many2one('res.partner', string='Provider 2')
    ide = fields.Char(string='ID')
    passwords_2 = fields.Char(string='Password')

    date_expiration = fields.Date(string="Starting Date")
    date_start = fields.Date(string="Expiration Date")
    comando_information = fields.Char(string="")

    acces_image = fields.Html(string="Access Image")
    image = fields.Html(string="Archivo")


    operation_wifi = fields.Boolean(string='Operator´s Wifi')
    network = fields.Char(string="Network")
    passwords_3 = fields.Char(string='Password')

    operation_lan = fields.Boolean(string='Operator´s Lan')
    ip_addres = fields.Html(string="IP Address")

    internet_service = fields.Boolean(string='ISP Internet Service Provider by Client')
    network_2 = fields.Html(string="Network")
    passwords_4 = fields.Char(string='Password')

    internet_service_obvio = fields.Boolean(string='ISP Internet Service Provider By Obvio')
    internet_provide = fields.Many2one('res.partner', string='Internet Provider')
    plan = fields.Char(string='Plan')
    phone_name = fields.Char(string='Tel Number')
    login_web = fields.Char(string='Provider Login Website')
    user_internet = fields.Char(string='User')
    pass_internet = fields.Char(string='Password')
    router_model = fields.Char(string='Router Model')
    user_internet_1 = fields.Char(string='User')
    pass_internet_2 = fields.Char(string='Password')
    device_router = fields.Binary(string='Device/Router', attachment=True)
    mode_especifique = fields.Binary(string='Model/Specifications', attachment=True)
    date_service_start = fields.Date(string="Starting Date")
    date_service_completo = fields.Date(string="Completion Date")
    contract = fields.Binary(string='Contract', attachment=True)



    @api.model_create_multi
    def create(self, vals_list):
        equipments = self.env['maintenance.equipment']  # Para almacenar los equipos creados
        for vals in vals_list:
            # Crear el equipo con el método original
            equipment = super(MaintenanceEquipment, self).create(vals)
            equipments += equipment #añadimos a la lista

            # Si existe un alias y el name_equipment, se añaden al nombre
            if equipment.type_equipment and equipment.type_equipment.alias_name:
                alias = equipment.type_equipment.alias_name
                name_parts = equipment.name.split(' - ')

                # Añadir el alias si no está en el nombre
                if alias not in name_parts:
                    name_parts.insert(1, alias)

                # Añadir el name_equipment después del alias si no está en el nombre
                if equipment.name_equipment and equipment.name_equipment not in name_parts:
                    name_parts.insert(2, equipment.name_equipment)

                # Actualizar el nombre
                equipment.name = ' - '.join(name_parts)
        return equipments



  

    #esta funciona
    """def write(self, vals):
        for equipment in self:
            # Descomponer el nombre en partes para separar el alias y las demás partes
            name_parts = equipment.name.split(' - ')
            client_part = name_parts[0] if name_parts else ''
            # Identificar y eliminar el alias antiguo si existe
            current_alias = equipment.type_equipment.alias_name if equipment.type_equipment else ''
            if current_alias in name_parts:
                name_parts.remove(current_alias)
            # Actualizar el tipo de equipo
            result = super(MaintenanceEquipment, self).write(vals)
            # Reemplazar el alias si se ha cambiado el tipo de equipo
            if 'type_equipment' in vals:
                new_type = self.env['equipment.type'].browse(vals['type_equipment'])
                new_alias = new_type.alias_name if new_type else ''
                # Insertar el nuevo alias solo si existe
                if new_alias:
                    name_parts.insert(1, new_alias)
                equipment.name = ' - '.join(name_parts).strip(' - ')

        return result"""

    def write(self, vals):
        for equipment in self:
            # Obtener los valores actuales del equipo
            current_name = equipment.name
            current_alias = equipment.type_equipment.alias_name if equipment.type_equipment else ''
            current_name_equipment = equipment.name_equipment if equipment.name_equipment else ''

            # Descomponer el nombre en partes para separar el alias y el nombre del equipo
            name_parts = current_name.split(' - ')

            # Si se actualiza el 'type_equipment', ajustamos el alias
            if 'type_equipment' in vals:
                new_alias = self.env['equipment.type'].browse(vals['type_equipment']).alias_name
                # Si el nuevo alias es diferente al actual, lo reemplazamos
                if new_alias != current_alias:
                    if current_alias in name_parts:
                        name_parts.remove(current_alias)
                    name_parts.insert(1, new_alias)

            # Si se actualiza el 'name_equipment', ajustamos el nombre del equipo
            if 'name_equipment' in vals:
                new_name_equipment = vals['name_equipment']
                # Si el nuevo nombre del equipo es diferente al actual, lo reemplazamos
                if new_name_equipment != current_name_equipment:
                    if current_name_equipment in name_parts:
                        name_parts.remove(current_name_equipment)
                    name_parts.insert(2, new_name_equipment)

            # Actualizar el nombre completo con las partes ajustadas
            vals['name'] = ' - '.join(name_parts).strip(' - ')

            # Llamamos al método `write` del modelo base para guardar los cambios
            return super(MaintenanceEquipment, self).write(vals)     



    @api.depends('type_equipment')
    def _compute_show_dss_tab(self):
        for record in self:
            if record.type_equipment and record.type_equipment.alias_name == 'DSS':
                record.show_dss_tab = True
            else:
                record.show_dss_tab = False


class MaintenanceEquipmentImage(models.Model):
    _name = 'maintenance.equipment.image'
    _description = 'Imágenes adjuntas a los equipos de mantenimiento'
   

    equipment_id = fields.Many2one('maintenance.equipment',required=True, ondelete='cascade')
    image = fields.Binary(string='Imagen', attachment=True)
    image_pdf = fields.Binary(string='Archivo', attachment=True)
    image_pdf_filename = fields.Char(string="Pdf Filename")
    name = fields.Char(string='Nombre')
    information = fields.Char(string='Nota')
    date_imagen = fields.Datetime(string="Fecha y Hora", default=fields.Datetime.now)
    video_filename = fields.Char(string="Video Filename")
    video_file = fields.Binary(string="Video")

class MaintenanceEquipmentImageTechnical(models.Model):
    _name = 'maintenance.equipment.image.technical'
    _description = 'Imágenes adjuntas a los equipos de mantenimiento en technical'
   

    technical_id = fields.Many2one('maintenance.equipment', required=True, ondelete='cascade')
    image = fields.Binary(string='Imagen', attachment=True)
    image_pdf = fields.Binary(string='Archivo', attachment=True)
    image_pdf_filename = fields.Char(string="Pdf Filename")
    name = fields.Char(string='Nombre')
    information = fields.Char(string='Nota')
    date_imagen = fields.Datetime(string="Fecha y Hora", default=fields.Datetime.now)
    video_filename = fields.Char(string="Video Filename")
    video_file = fields.Binary(string="Video")


class MaintenanceEquipmentImageTechnical(models.Model):
    _name = 'maintenance.equipment.image.hardware'
    _description = 'Imágenes adjuntas a los equipos de mantenimiento en hardware'
   

    hardware_id = fields.Many2one('maintenance.equipment', required=True, ondelete='cascade')
    image = fields.Binary(string='Imagen', attachment=True)
    image_pdf = fields.Binary(string='Archivo', attachment=True)
    image_pdf_filename = fields.Char(string="Pdf Filename")
    name = fields.Char(string='Nombre')
    information = fields.Char(string='Nota')
    date_imagen = fields.Datetime(string="Fecha y Hora", default=fields.Datetime.now)
    video_filename = fields.Char(string="Video Filename")
    video_file = fields.Binary(string="Video")