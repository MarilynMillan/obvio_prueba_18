from odoo import api, fields, models, _
from odoo import models, fields, api, _
from odoo.exceptions import UserError

class ProjectProject(models.Model):
    _inherit = 'project.project'
    _order = "name asc"



    partner_id = fields.Many2one(
        'res.partner', 
        string='Customer',domain=[('customer_is', '=', True)])
    maintenance_equipment_ids = fields.One2many(
        'maintenance.equipment',
        'project_id',
        string='Equipment creation'
    )

    partner_operator_id = fields.Many2one(
        'res.partner', 
        string='Operator',
        domain=[('is_operator', '=', True)]  # Solo mostrar contactos que son operadores
    )
    create_equipment = fields.Boolean(string='Create equipment', default=False)
    #sequence = fields.Char(string='Correlativo', readonly=True, copy=False)
    operation = fields.Char(string='Operator')
    zona_id = fields.Many2one('project.zone', string='Country')
    ubication_id = fields.Many2one(
        'zone.ubication',
        string='Location',
        domain="[('zone_id', '=', zona_id)]"
    )
    tienda_id = fields.Many2one(
        'zone.tienda',
        string='Store',
        domain="[('ubication_id', '=', ubication_id)]"
    )
    type_project = fields.Many2one('type.project', string='Project type')
    company_id = fields.Many2one(
        'res.company',
        string='Company',
        default=lambda self: self.env.company,
        required=True,
        index=True
    )
    template_project_id = fields.Many2one(
    'project.project',
    string='Project template',
    domain="[('is_template', '=', True)]",
    help="Selecciona un proyecto marcado como plantilla.")
    is_template = fields.Boolean(
    string='Is template',
    default=False,
    help="If checked, this project can be used as a template.")
    original_name = fields.Char(string='Original name', copy=False)
    name_copy = fields.Char(string='Short name',help="Short project name. Used in automatic naming.")
    sequence_new = fields.Char(string='Sequence', readonly=True, copy=False)
    priority = fields.Selection([
        ('0', 'very low'),
        ('1', 'Low'),
        ('2', 'High'),
        ('3', 'Very High'),
    ], string="Prioridad")


    @api.onchange('template_project_id')
    def _onchange_template_project_id(self):
        if self.template_project_id:
            return {
                'warning': {
                    'title': _('Validation'),
                    'message': _(
                        "Please make sure the template '%s', is the correct one."
                    ) % self.template_project_id.name
                }
            }

     # 1. Onchange para el País/Zona
    @api.onchange('zona_id')
    def _onchange_zona_id(self):
        """
        Limpia la Localidad y la Tienda si la Localidad actual no pertenece
        al nuevo País/Zona.
        """
        # Limpia Localidad si el valor actual no está en el nuevo País/Zona.
        if self.ubication_id and self.ubication_id.zone_id != self.zona_id:
            self.ubication_id = False
        


    @api.onchange('is_template', 'name_copy', 'type_project', 'partner_id', 'partner_operator_id', 'zona_id', 'tienda_id', 'ubication_id', 'is_subproject', 'parent_project_id', 'subproject_suffix')
    def _onchange_nomenclatura(self):
        """
        Actualiza el campo 'name' dinámicamente en la vista cuando el usuario edita
        el nombre corto o cualquier campo de la nomenclatura.
        """
        for project in self:
            is_template = project.is_template
            project_name_short = project.name_copy or project.original_name

            if is_template:
                project.name = "TEMPLATE - " + (project_name_short or '')
                continue

            # Determinación temporal del correlativo
            sequence_new = project.sequence_new or '/'
            if project.is_subproject and project.parent_project_id:
                parent = project.parent_project_id
                suffix = (project.subproject_suffix or '').strip()
                if parent.sequence_new and parent.sequence_new != 'TEMPLATE':
                    base_sequence = parent.sequence_new
                    parts = base_sequence.split(' ')
                    if parts and parts[-1].isalpha() and len(parts[-1]) <= 2:
                        base_sequence = ' '.join(parts[:-1])
                    sequence_new = f"{base_sequence} {suffix}" if suffix else base_sequence

            # Construir el nombre completo en orden fijo
            type_project_alias = project.type_project.alias_name if project.type_project else ''
            partner_alias = project.partner_id.alias_name if project.partner_id else ''
            operator_code = project.partner_operator_id.codigo_operator if project.partner_operator_id else ''
            zona_info = project.zona_id.code if project.zona_id else ''
            tienda_name = project.tienda_id.tienda if project.tienda_id else ''
            ubication_name = project.ubication_id.zone if project.ubication_id else ''

            name_parts = [sequence_new]
            if type_project_alias: name_parts.append(type_project_alias)
            if partner_alias: name_parts.append(partner_alias)
            if project_name_short: name_parts.append(project_name_short)
            if operator_code: name_parts.append(operator_code)
            if tienda_name: name_parts.append(tienda_name)
            if ubication_name: name_parts.append(ubication_name)
            if zona_info: name_parts.append(zona_info)

            project.name = " - ".join(part for part in name_parts if part)

    # 2. Onchange para la Localidad
    @api.onchange('ubication_id')
    def _onchange_ubication_id(self):
        """
        Limpia la Tienda si la Tienda actual no pertenece a la nueva Localidad.
        """
        # Limpia Tienda si el valor actual no está en la nueva Localidad.
        if self.tienda_id and self.tienda_id.ubication_id != self.ubication_id:
            self.tienda_id = False

        # Si ubication_id cambia, también nos aseguramos de que el País/Zona esté asociado
        # (Aunque el dominio en la vista ya ayuda con esto, es una buena práctica defensiva).
        if self.ubication_id and self.ubication_id.zone_id != self.zona_id:
            self.zona_id = self.ubication_id.zone_id

    @api.constrains('zona_id', 'ubication_id', 'tienda_id')
    def _check_location_hierarchy(self):
        """
        Verifica la coherencia entre País, Localidad y Tienda.
        Se ejecuta en create y write.
        """
        for record in self:
            # 1. Verificar Localidad vs. País (Zona)
            if record.ubication_id and record.ubication_id.zone_id != record.zona_id:
                if record.zona_id:
                    raise UserError(
                        ("The Location"
                         f"'{record.ubication_id.display_name}' does not belong to the country "
                         f"'{record.zona_id.display_name}'.")
                    )
                else:
                    raise UserError(
                        ("You must select a country "
                         f"Valid for the Locality '{record.ubication_id.display_name}'.")
                    )

            # 2. Verificar Tienda vs. Localidad
            if record.tienda_id and record.tienda_id.ubication_id != record.ubication_id:
                if record.ubication_id:
                    raise UserError(
                        ("The Store "
                         f"'{record.tienda_id.display_name}' it is not associated with the locality. "
                         f"'{record.ubication_id.display_name}'.")
                    )
                else:
                    raise UserError(
                        ("You must select a location "
                         f"Valid for the Store '{record.tienda_id.display_name}'.")
                    )

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            # --- 1. LÓGICA DE PLANTILLA ---
            if vals.get('is_template'):
                vals['sequence_new'] = 'TEMPLATE'
                vals['account_id'] = False

                # --- BLINDAJE PARA DOCUMENTOS ---
                # Esto evita que Odoo Enterprise Documents cree el workspace
                # y bloquee el autovacuum después.
                vals['use_documents'] = False
                vals['documents_folder_id'] = False

            # --- 2. DETERMINAR EL CORRELATIVO ---
            elif vals.get('is_subproject') and vals.get('parent_project_id'):
                parent = self.env['project.project'].browse(vals['parent_project_id'])
                suffix = vals.get('subproject_suffix', '').strip()

                if parent.sequence_new and parent.sequence_new != 'TEMPLATE':
                    base_sequence = parent.sequence_new
                    parts = base_sequence.split(' ')
                    if parts and parts[-1].isalpha() and len(parts[-1]) <= 2:
                        base_sequence = ' '.join(parts[:-1])
                    vals['sequence_new'] = f"{base_sequence} {suffix}" if suffix else base_sequence
                else:
                    vals['sequence_new'] = self.env['ir.sequence'].next_by_code('project.project') or '/'

            else:
                if not vals.get('sequence_new') or vals['sequence_new'] in ['New', '/', False]:
                    vals['sequence_new'] = self.env['ir.sequence'].next_by_code('project.project') or '/'

            # --- 3. NOMENCLATURA (Se mantiene tu lógica intacta) ---
            vals['original_name'] = vals.get('name', '')
            vals['name_copy'] = vals.get('name', '')

            # Búsquedas de alias
            type_project_alias = self.env['type.project'].browse(vals.get('type_project', False)).alias_name or ''
            partner_alias = self.env['res.partner'].browse(vals.get('partner_id', False)).alias_name or ''
            operator_code = self.env['res.partner'].browse(vals.get('partner_operator_id', False)).codigo_operator or ''
            zona_info = self.env['project.zone'].browse(vals.get('zona_id', False)).code or ''
            tienda_name = self.env['zone.tienda'].browse(vals.get('tienda_id', False)).tienda or ''
            ubication_name = self.env['zone.ubication'].browse(vals.get('ubication_id', False)).zone or ''
            project_name_short = vals['name_copy']

            if vals.get('is_template'):
                vals['name'] = "TEMPLATE - " + (project_name_short or vals.get('original_name') or '')
            else:
                name_parts = [vals['sequence_new']]
                if type_project_alias: name_parts.append(type_project_alias)
                if partner_alias: name_parts.append(partner_alias)
                if project_name_short: name_parts.append(project_name_short)
                if operator_code: name_parts.append(operator_code)
                if tienda_name: name_parts.append(tienda_name)
                if ubication_name: name_parts.append(ubication_name)
                if zona_info: name_parts.append(zona_info)

                vals['name'] = " - ".join(part for part in name_parts if part)

        # Crear proyectos
        projects = super(ProjectProject, self).create(vals_list)

        # --- 4. POST-CREACIÓN ---
        for vals, project in zip(vals_list, projects):
            if project.is_template:
                # Doble validación: aseguramos que no quede cuenta ni documentos
                project.write({
                    'account_id': False,
                    'use_documents': False,
                    'documents_folder_id': False
                })
                continue

            # Actualizar nombre de cuenta analítica (proyectos normales)
            if project.account_id:
                project.account_id.name = project.name

            # Copiar tareas si viene de una plantilla
            if vals.get('template_project_id'):
                template_project = self.env['project.project'].browse(vals['template_project_id'])
                if template_project:
                    for task in template_project.task_ids:
                        task.with_context(copy_project=True).copy({
                            'project_id': project.id,
                            'name': task.name,
                            'stage_id': task.stage_id.id,
                            'sequence': task.sequence,
                            'tag_ids': [(6, 0, task.tag_ids.ids)],
                            'user_ids': [(6, 0, task.user_ids.ids)],
                        })
        return projects

    def unlink(self):
        return super(ProjectProject, self.with_context(is_unlinking_parent=True)).unlink()

    def write(self, vals):

        protected_fields = [
            'operation', 'zona_id', 'ubication_id', 'tienda_id',
            'type_project', 'partner_id', 'partner_operator_id'
        ]

        # Validar seguridad solo si el usuario NO es manager.
        # El responsable del proyecto puede editar campos críticos en sus propios proyectos.
        if not self.env.user.has_group('project.group_project_manager'):
            current_user = self.env.user
            for project in self:
                # Si el proyecto NO es plantilla y intentan cambiar un campo protegido
                if (
                    not project.is_template
                    and any(f in vals for f in protected_fields)
                    and project.user_id != current_user
                ):
                    raise UserError(_("You cannot modify critical fields in an active project. Contact a Manager."))

        # Evitar que se asigne una cuenta si el proyecto se marca como plantilla
        if vals.get('is_template'):
            vals['account_id'] = False
            vals['sequence_new'] = 'TEMPLATE'

        res = super(ProjectProject, self).write(vals)

        campos_nomenclatura = [
            'type_project', 'partner_id', 'partner_operator_id', 'zona_id',
            'tienda_id', 'ubication_id', 'name_copy', 'is_subproject',
            'parent_project_id', 'subproject_suffix'
        ]

        if any(campo in vals for campo in campos_nomenclatura):
            for project in self:
                is_template = vals.get('is_template', project.is_template)

                if is_template:
                    # Renombramos con el formato de plantilla
                    project_name_short = project.name_copy or project.original_name
                    new_name = "TEMPLATE - " + (project_name_short or '')
                    if new_name != project.name:
                        super(ProjectProject, project).write({'name': new_name})
                    continue

                sequence_new = project.sequence_new
                is_subproject = vals.get('is_subproject', getattr(project, 'is_subproject', False))

                if is_subproject:
                    parent_id = vals.get('parent_project_id', getattr(project, 'parent_project_id', False))
                    if hasattr(parent_id, 'id'):
                        parent_id = parent_id.id

                    suffix = vals.get('subproject_suffix', getattr(project, 'subproject_suffix', '') or '').strip()
                    if parent_id:
                        parent = self.env['project.project'].browse(parent_id)
                        if parent.sequence_new and parent.sequence_new != 'TEMPLATE':
                            base_seq = parent.sequence_new
                            parts = base_seq.split(' ')
                            if parts and parts[-1].isalpha() and len(parts[-1]) <= 2:
                                base_seq = ' '.join(parts[:-1])
                            sequence_new = f"{base_seq} {suffix}" if suffix else base_seq

                # Reconstrucción de nombre (tu lógica original)
                type_alias = self.env['type.project'].browse(vals.get('type_project', project.type_project.id)).alias_name or ''
                partner_alias = self.env['res.partner'].browse(vals.get('partner_id', project.partner_id.id)).alias_name or ''
                op_code = self.env['res.partner'].browse(vals.get('partner_operator_id', project.partner_operator_id.id)).codigo_operator or ''
                z_info = self.env['project.zone'].browse(vals.get('zona_id', project.zona_id.id)).code or ''
                t_name = self.env['zone.tienda'].browse(vals.get('tienda_id', project.tienda_id.id)).tienda or ''
                u_name = self.env['zone.ubication'].browse(vals.get('ubication_id', project.ubication_id.id)).zone or ''
                p_short = project.name_copy or project.original_name

                name_parts = [sequence_new]
                if type_alias: name_parts.append(type_alias)
                if partner_alias: name_parts.append(partner_alias)
                if p_short: name_parts.append(p_short)
                if op_code: name_parts.append(op_code)
                if t_name: name_parts.append(t_name)
                if u_name: name_parts.append(u_name)
                if z_info: name_parts.append(z_info)

                new_name = " - ".join(part for part in name_parts if part)

                super(ProjectProject, project).write({'name': new_name, 'sequence_new': sequence_new})

                if getattr(project, 'account_id', False):
                    project.account_id.name = new_name
        return res

    def create_maintenance_equipment(self):
        self.ensure_one()  # Asegura que solo se esté trabajando con un registro a la vez

        # Obtener los valores necesarios
        partner_alias = self.partner_id.alias_name or ''
        country_code = self.zona_id.code or ''  # Código del país
        zone_name = self.ubication_id.zone or ''  # Nombre de la zona
        tienda_name = self.tienda_id.tienda or ''  # Nombre de la tienda
        operator_code = self.partner_operator_id.codigo_operator or ''  # Código del operador

        # Construir la información de zona, tienda y país
        zona_info = f"{tienda_name} - {zone_name} - {country_code}"

        # Concatenar el nombre del equipo
        equipment_name = f"{partner_alias} - {operator_code} - {zona_info}"

        # Crear un nuevo equipo y asociarlo con el proyecto
        equipment = self.env['maintenance.equipment'].create({
            'name': equipment_name,
            'project_id': self.id,  # Asociar el equipo con el proyecto
            'project_sequence': self.sequence_new,  # Guardar la secuencia del proyecto en el nuevo campo
            # Agrega otros campos necesarios aquí
        })

        # Retornar una acción para abrir la vista de formulario del equipo creado
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'maintenance.equipment',
            'view_mode': 'form',
            'view_id': self.env.ref('maintenance.hr_equipment_view_form').id,  # Especificar el ID de la vista de formulario
            'res_id': equipment.id,
            'target': 'current',
        }