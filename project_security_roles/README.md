# Documentacion funcional de reglas de permisos (Proyecto)

Este documento resume, en lenguaje funcional, las reglas creadas para usuarios de tipo **Project / User** y su alcance por modulo.

## 1) Regla base en Proyectos

Modulo: `project_security_roles`

- **Own Projects Edit**
  Permite administrar (crear, editar, eliminar) solo los proyectos donde el usuario es responsable.
- **Follower Projects Read**
  Permite ver proyectos donde el usuario es seguidor, sin capacidad de edicion.
- **Team Projects Read**
  Permite ver proyectos por criterio de equipo compartido (team), sin capacidad de edicion.

Reglas funcionales relacionadas en el mismo modulo:
- **Own Tasks Edit**: administra tareas de sus propios proyectos.
- **Assigned Tasks Write**: puede gestionar tareas en las que esta asignado.
- **Own Milestones Edit**: administra hitos de sus propios proyectos.
- **Own Project Updates Edit**: administra objetivos/actualizaciones de sus propios proyectos.
- **Follower Project Updates Read**: lectura de objetivos/actualizaciones en proyectos seguidos.
- **Team Project Updates Read**: lectura de objetivos/actualizaciones por criterio de team.

## 2) Reglas para Documentos de Proyecto

Modulo: `project_security_roles_documents`

- **Project Documents Scoped Read**
  Permite ver documentos de proyectos visibles para el usuario (propios, seguidos o team), sin editar.
- **Project Documents Manager Full Read**
  Mantiene lectura total para Project Manager.

## 3) Reglas para Forecast (Planificacion)

Modulo: `project_security_roles_forecast`

- Regla funcional de gestion:
  el usuario puede administrar forecast solo en proyectos propios.
- Regla funcional de lectura:
  el usuario puede ver forecast en proyectos que sigue o donde aplica criterio de team.
- Regla adicional:
  lectura de plantillas de forecast segun el mismo alcance funcional.

## 4) Reglas para Timesheets

Modulo: `project_security_roles_timesheet`

- **Own Project Timesheets Manage**
  Permite administrar horas solo en proyectos propios.
- **Project Timesheets Scoped Read**
  Permite ver horas en proyectos propios, seguidos o de team.
- **Project Timesheets Report Scoped Read**
  Aplica el mismo criterio de lectura al reporte de horas.

## 5) Reglas para reporte Timesheet + Forecast

Modulo: `project_security_roles_timesheet_forecast`

- **Project Timesheet Forecast Report Scoped Read**
  Permite ver el analisis combinado de horas y planificacion solo para proyectos propios, seguidos o de team.
- **Project Timesheet Forecast Report Manager Full Read**
  Mantiene lectura completa para Project Manager.

## Resultado funcional esperado

- Un usuario de tipo **Project / User** administra solo lo propio.
- Puede ver informacion de proyectos seguidos y de team en modo lectura.
- Un **Project Manager** conserva visibilidad completa.
