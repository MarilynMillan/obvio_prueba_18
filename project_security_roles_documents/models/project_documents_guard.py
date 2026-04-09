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

    def _can_manage_project_related_record(self, model_name, res_id, user):
        if not model_name or not res_id:
            return False
        if model_name not in self._PROJECT_GUARDED_MODELS:
            return False

        record = self.env[model_name].sudo().browse(res_id).exists()
        if not record:
            return False

        # Validación por responsabilidad de proyecto
        if model_name == "project.project":
            return record.user_id == user
        if model_name == "project.task":
            return record.project_id.user_id == user
        if hasattr(record, 'project_id'):
            return record.project_id.user_id == user
        return False

    def _get_target_model_res_id_from_vals(self, vals, record=None):
        model_name = vals.get("res_model") if vals else None
        res_id = vals.get("res_id") if vals else None
        if record:
            model_name = model_name if model_name is not None else record.res_model
            res_id = res_id if res_id is not None else record.res_id

        if (not model_name or not res_id) and vals and vals.get("attachment_id"):
            attachment = self.env["ir.attachment"].sudo().browse(vals["attachment_id"]).exists()
            if attachment:
                model_name = model_name or attachment.res_model
                res_id = res_id or attachment.res_id

        return model_name, res_id

    @api.model_create_multi
    def create(self, vals_list):
        if self._is_project_user_restricted():
            user = self.env.user
            for vals in vals_list:
                model_name, res_id = self._get_target_model_res_id_from_vals(vals)
                if model_name in self._PROJECT_GUARDED_MODELS:
                    if not self._can_manage_project_related_record(model_name, res_id, user):
                        raise AccessError(_("No puedes crear documentos en proyectos que no gestionas."))
        return super().create(vals_list)

    def write(self, vals):
        if self._is_project_user_restricted():
            user = self.env.user
            my_records = self.filtered(lambda r: r.owner_id == user)
            others_records = self - my_records

            res = True
            if my_records:
                res = super(DocumentsDocument, my_records).write(vals)

            if others_records:
                for record in others_records:
                    model_name, res_id = self._get_target_model_res_id_from_vals(vals, record=record)
                    if not self._can_manage_project_related_record(model_name, res_id, user):
                        raise AccessError(_("No puedes modificar, mover ni renombrar carpetas o archivos de otros usuarios que no gestionas."))

                res = super(DocumentsDocument, others_records).write(vals) and res

            return res

        return super(DocumentsDocument, self).write(vals)

    def _check_access(self, operation):
        if self.env.user.has_group("project.group_project_user") and not self.env.user.has_group("project.group_project_manager"):
            return

        if hasattr(super(DocumentsDocument, self), '_check_access'):
            return super(DocumentsDocument, self)._check_access(operation)
        return None

    def unlink(self):
        if self._is_project_user_restricted():
            user = self.env.user
            for record in self:
                if record.owner_id == user:
                    continue
                model_name, res_id = self._get_target_model_res_id_from_vals({}, record=record)
                if not self._can_manage_project_related_record(model_name, res_id, user):
                    raise AccessError(_("No tienes permisos para eliminar documentos o carpetas de terceros."))
        return super().unlink()


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
