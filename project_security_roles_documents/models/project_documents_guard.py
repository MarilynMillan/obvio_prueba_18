from odoo import _, api, models
from odoo.exceptions import AccessError


class DocumentsDocument(models.Model):
    _inherit = "documents.document"

    _PROJECT_GUARDED_MODELS = {
        "project.project",
        "project.task",
        "project.milestone",
        "project.update",
    }

    def _is_project_user_restricted(self):
        user = self.env.user
        return user.has_group("project.group_project_user") and not user.has_group(
            "project.group_project_manager"
        )

    # --- INDISPENSABLE EN ODOO 18 PARA ARRASTRAR ---
    def _check_access(self, operation):
        if self.env.user.has_group("project.group_project_user"):
            return # Permite la navegación y el movimiento visual
        return super(DocumentsDocument, self)._check_access(operation)

    def write(self, vals):
        # 1. Si es Admin o Manager, no hacemos nada y dejamos pasar
        if not self._is_project_user_restricted():
            return super(DocumentsDocument, self).write(vals)

        user = self.env.user
        # 2. Separamos: lo que creó el PM vs lo que no
        my_records = self.filtered(lambda r: r.owner_id == user)
        others_records = self - my_records

        # 3. LO QUE ES MÍO: Lo muevo con sudo() para que Odoo me deje 'entrar' en carpetas ajenas
        if my_records:
            super(DocumentsDocument, my_records.sudo()).write(vals)

        # 4. LO QUE NO ES MÍO: Bloqueo si intenta moverlo o renombrarlo
        if others_records:
            fields_to_block = ['parent_id', 'folder_id', 'name', 'owner_id']
            if any(f in vals for f in fields_to_block):
                raise AccessError(_("No tienes permisos para mover o modificar documentos de otros usuarios."))
            
            # Si solo cambia etiquetas, permitimos
            super(DocumentsDocument, others_records).write(vals)
        
        return True

    def unlink(self):
        if self._is_project_user_restricted():
            user = self.env.user
            if any(record.owner_id != user for record in self):
                raise AccessError(_("No puedes eliminar documentos de otros usuarios."))
        return super(DocumentsDocument, self).unlink()


class MailMessage(models.Model):
    _inherit = "mail.message"

    def _is_project_user_restricted(self):
        user = self.env.user
        return user.has_group("project.group_project_user") and not user.has_group(
            "project.group_project_manager"
        )

    def _can_manage_documents_message(self, model_name, res_id, user):
        if model_name != "documents.document" or not res_id:
            return True
        document = self.env["documents.document"].sudo().browse(res_id).exists()
        if not document:
            return False
        doc_model = document.res_model
        doc_res_id = document.res_id
        if doc_model not in DocumentsDocument._PROJECT_GUARDED_MODELS:
            return True
        return self.env["documents.document"]._can_manage_project_related_record(
            doc_model, doc_res_id, user
        )

    def _check_documents_message_guard(self, candidates):
        if not self._is_project_user_restricted():
            return
        user = self.env.user
        for model_name, res_id in candidates:
            if not self._can_manage_documents_message(model_name, res_id, user):
                raise AccessError(
                    _(
                        "You can only manage chatter messages on documents linked to project records where you are the project responsible."
                    )
                )

    @api.model_create_multi
    def create(self, vals_list):
        candidates = [
            (vals.get("model"), vals.get("res_id")) for vals in vals_list if vals.get("model")
        ]
        self._check_documents_message_guard(candidates)
        return super().create(vals_list)

    def write(self, vals):
        candidates = []
        for message in self:
            candidates.append((vals.get("model", message.model), vals.get("res_id", message.res_id)))
        self._check_documents_message_guard(candidates)
        return super().write(vals)

    def unlink(self):
        candidates = [(message.model, message.res_id) for message in self]
        self._check_documents_message_guard(candidates)
        return super().unlink()


class IrAttachment(models.Model):
    _inherit = "ir.attachment"

    def _is_project_user_restricted(self):
        user = self.env.user
        return user.has_group("project.group_project_user") and not user.has_group(
            "project.group_project_manager"
        )

    def _can_manage_documents_attachment(self, model_name, res_id, user):
        if model_name != "documents.document" or not res_id:
            return True
        document = self.env["documents.document"].sudo().browse(res_id).exists()
        if not document:
            return False
        doc_model = document.res_model
        doc_res_id = document.res_id
        if doc_model not in DocumentsDocument._PROJECT_GUARDED_MODELS:
            return True
        return self.env["documents.document"]._can_manage_project_related_record(
            doc_model, doc_res_id, user
        )

    def _check_documents_attachment_guard(self, vals_list=None, records=None):
        if not self._is_project_user_restricted():
            return
        user = self.env.user

        if vals_list:
            for vals in vals_list:
                model_name = vals.get("res_model")
                res_id = vals.get("res_id")
                if not self._can_manage_documents_attachment(model_name, res_id, user):
                    raise AccessError(
                        _(
                            "You can only manage attachments on documents linked to project records where you are the project responsible."
                        )
                    )

        if records:
            for attachment in records:
                if not self._can_manage_documents_attachment(
                    attachment.res_model, attachment.res_id, user
                ):
                    raise AccessError(
                        _(
                            "You can only manage attachments on documents linked to project records where you are the project responsible."
                        )
                    )

    @api.model_create_multi
    def create(self, vals_list):
        self._check_documents_attachment_guard(vals_list=vals_list)
        return super().create(vals_list)

    def write(self, vals):
        if self._is_project_user_restricted():
            user = self.env.user
            for attachment in self:
                model_name = vals.get("res_model", attachment.res_model)
                res_id = vals.get("res_id", attachment.res_id)
                if not self._can_manage_documents_attachment(model_name, res_id, user):
                    raise AccessError(
                        _(
                            "You can only manage attachments on documents linked to project records where you are the project responsible."
                        )
                    )
        return super().write(vals)

    def unlink(self):
        self._check_documents_attachment_guard(records=self)
        return super().unlink()


class MailActivity(models.Model):
    _inherit = "mail.activity"

    def _is_project_user_restricted(self):
        user = self.env.user
        return user.has_group("project.group_project_user") and not user.has_group(
            "project.group_project_manager"
        )

    def _can_manage_documents_activity(self, model_name, res_id, user):
        if model_name != "documents.document" or not res_id:
            return True
        document = self.env["documents.document"].sudo().browse(res_id).exists()
        if not document:
            return False
        doc_model = document.res_model
        doc_res_id = document.res_id
        if doc_model not in DocumentsDocument._PROJECT_GUARDED_MODELS:
            return True
        return self.env["documents.document"]._can_manage_project_related_record(
            doc_model, doc_res_id, user
        )

    def _check_documents_activity_guard(self, vals_list):
        if not self._is_project_user_restricted():
            return
        user = self.env.user
        for vals in vals_list:
            model_name = vals.get("res_model")
            if not model_name and vals.get("res_model_id"):
                model_name = self.env["ir.model"].sudo().browse(vals["res_model_id"]).model
            res_id = vals.get("res_id")
            if not self._can_manage_documents_activity(model_name, res_id, user):
                raise AccessError(
                    _(
                        "You can only schedule activities on documents linked to project records where you are the project responsible."
                    )
                )

    @api.model_create_multi
    def create(self, vals_list):
        self._check_documents_activity_guard(vals_list)
        return super().create(vals_list)

    def write(self, vals):
        vals_list = []
        for activity in self:
            candidate = dict(vals)
            candidate.setdefault("res_model", activity.res_model)
            candidate.setdefault("res_id", activity.res_id)
            vals_list.append(candidate)
        self._check_documents_activity_guard(vals_list)
        return super().write(vals)


