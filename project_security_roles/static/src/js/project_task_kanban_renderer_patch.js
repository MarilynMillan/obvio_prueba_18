/** @odoo-module */

import { registry } from "@web/core/registry";
import { ProjectTaskKanbanRenderer } from "@project/views/project_task_kanban/project_task_kanban_renderer";
import { useService } from "@web/core/utils/hooks";
import { onWillStart } from "@odoo/owl";
import { user } from "@web/core/user";

class ProjectSecurityRolesTaskKanbanRenderer extends ProjectTaskKanbanRenderer {
    setup() {
        super.setup();
        this.orm = useService("orm");
        this.isProjectOwner = false;
        onWillStart(async () => {
            try {
                if (!this.isProjectTasksContext()) {
                    this.isProjectOwner = false;
                    return;
                }
                const projectId = this.props.list.context.default_project_id;
                if (!projectId) {
                    this.isProjectOwner = false;
                    return;
                }
                const [project] = await this.orm.read("project.project", [projectId], ["user_id"]);
                this.isProjectOwner = Boolean(project?.user_id?.[0] === user.userId);
            } catch {
                this.isProjectOwner = false;
            }
        });
    }

    canCreateGroup() {
        const groupByField = this.props.list.groupByField;
        const canCreateGroupByAcl =
            this.props.archInfo?.activeActions?.createGroup &&
            groupByField?.type === "many2one";
        if (!canCreateGroupByAcl) {
            return false;
        }
        if (groupByField?.name === "personal_stage_type_id") {
            return true;
        }
        const isProjectStageColumnContext =
            this.isProjectTasksContext() === this.props.list.isGroupedByStage;
        if (!isProjectStageColumnContext) {
            return false;
        }
        return this.isProjectManager || this.isProjectOwner;
    }
}

const viewsRegistry = registry.category("views");
const projectEnterpriseTaskKanbanView = viewsRegistry.get("project_enterprise_task_kanban");
viewsRegistry.add("project_security_roles_task_kanban", {
    ...projectEnterpriseTaskKanbanView,
    Renderer: ProjectSecurityRolesTaskKanbanRenderer,
});
