from odoo import api, fields, models, _
from datetime import datetime
from dateutil.relativedelta import relativedelta
from odoo.exceptions import ValidationError, UserError
from copy import deepcopy
import logging
from decimal import Decimal, ROUND_HALF_UP
_logger = logging.getLogger(__name__)

class SaleOrder(models.Model):
    _inherit = "sale.order"

    project_id = fields.Many2one(
        "project.project",
        string="Project",
        index=True,
        help="Linked project for this quotation/order.",
    )

    amount_total_words = fields.Char(
        string="Total in Words",
        compute="_compute_amount_total_words",
        store=False,
    )

    show_tax_column = fields.Boolean(string="Show Tax column", default=True)

    def _obvio_round_half_up(self, amount, digits=0):
        """Round half up (>= .5 up). digits=0 => entero."""
        q = Decimal("1") if digits == 0 else Decimal("1").scaleb(-digits)  # 10**(-digits)
        d = Decimal(str(amount or 0.0))
        return float(d.quantize(q, rounding=ROUND_HALF_UP))

    def _obvio_tax_totals_rounded(self, digits=0):
        """
        Devuelve una COPIA de tax_totals con montos redondeados (solo para reporte).
        No altera doc.tax_totals (UI).
        """
        self.ensure_one()
        if not self.tax_totals:
            return {}

        totals = deepcopy(self.tax_totals)

        # helper local
        def r(x):
            return self._obvio_round_half_up(x, digits)

        # subtotals (untaxed por subtotal)
        for subtotal in totals.get("subtotals", []) or []:
            if "base_amount_currency" in subtotal:
                subtotal["base_amount_currency"] = r(subtotal["base_amount_currency"])
            if "base_amount" in subtotal:
                subtotal["base_amount"] = r(subtotal["base_amount"])

            # tax_groups dentro del subtotal
            for tg in subtotal.get("tax_groups", []) or []:
                if "tax_amount_currency" in tg:
                    tg["tax_amount_currency"] = r(tg["tax_amount_currency"])
                if "tax_amount" in tg:
                    tg["tax_amount"] = r(tg["tax_amount"])

        # groups_by_subtotal
        gbs = totals.get("groups_by_subtotal") or {}
        for _k, groups in gbs.items():
            for tg in groups or []:
                if "tax_amount_currency" in tg:
                    tg["tax_amount_currency"] = r(tg["tax_amount_currency"])
                if "tax_amount" in tg:
                    tg["tax_amount"] = r(tg["tax_amount"])

        # total
        if "total_amount_currency" in totals:
            totals["total_amount_currency"] = r(totals["total_amount_currency"])
        if "total_amount" in totals:
            totals["total_amount"] = r(totals["total_amount"])

        return totals

    @api.model
    def _get_or_create_company_sequence(self, company):
        Sequence = self.env["ir.sequence"].sudo()
        code = "sale.order.obvio.quote"

        seq = Sequence.search([("code", "=", code), ("company_id", "=", company.id)], limit=1)
        template = Sequence.search([("code", "=", code), ("company_id", "=", False)], limit=1)

        if not template:
            raise UserError(_("Missing sequence template for code '%s' (data/sequence.xml).") % code)

        if not seq:
            seq = template.copy({
                "name": f"OBVIO Quotation ({company.display_name})",
                "company_id": company.id,
            })

        # Asegura configuración correcta aunque la secuencia ya existiera vieja
        vals_to_fix = {}
        if not seq.use_date_range:
            vals_to_fix["use_date_range"] = True
        if seq.prefix != template.prefix:
            vals_to_fix["prefix"] = template.prefix
        if vals_to_fix:
            seq.write(vals_to_fix)

        return seq

    @api.model
    def _normalize_sequence_datetime(self, vals):
        dt = vals.get("date_order")
        dt = fields.Datetime.to_datetime(dt) if dt else fields.Datetime.now()
        return dt

    @api.model
    def _ensure_monthly_date_range(self, seq, seq_dt):
        """
        Garantiza que exista un ir.sequence.date_range mensual para seq_dt.
        date_from/date_to se guardan como Date (inclusivo).
        """
        DateRange = self.env["ir.sequence.date_range"].sudo()

        d = seq_dt.date()
        month_start = d.replace(day=1)
        month_end = (month_start + relativedelta(months=1)) - relativedelta(days=1)

        dr = DateRange.search([
            ("sequence_id", "=", seq.id),
            ("date_from", "=", month_start),
            ("date_to", "=", month_end),
        ], limit=1)

        if not dr:
            dr = DateRange.create({
                "sequence_id": seq.id,
                "date_from": month_start,
                "date_to": month_end,
                "number_next": 1,
            })

        return dr

    @api.model
    def _to_short_year(self, seq_str):
        # '2026.03-001' -> '26.03-001'
        if seq_str and len(seq_str) >= 5 and seq_str[4] == ".":
            return seq_str[2:]
        return seq_str

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            name = vals.get("name", "New")
            if name not in (False, None, "/", "New"):
                continue

            company_id = vals.get("company_id") or self.env.company.id
            company = self.env["res.company"].browse(company_id)

            seq = self._get_or_create_company_sequence(company)
            seq_dt = self._normalize_sequence_datetime(vals)
            _logger.warning("SEQ DEBUG name=%s vals.date_order=%s seq_dt=%s", vals.get("name"), vals.get("date_order"),
                            seq_dt)

            # Crea rango mensual antes de pedir next_by_id
            self._ensure_monthly_date_range(seq, seq_dt)

            full = seq.with_company(company_id).next_by_id(sequence_date=seq_dt)
            vals["name"] = self._to_short_year(full)

        return super().create(vals_list)

    def action_autofill_lines_from_project(self):
        for o in self:
            if not o.project_id:
                continue
            p = o.project_id
            for l in o.order_line.filtered(lambda x: not x.display_type):
                l.write({
                    "market_id": p.zona_id.id or False,
                    "location_id": p.ubication_id.id or False,
                    "store_id": p.tienda_id.id or False,
                    "operator_id": p.partner_operator_id.id or False,
                })

    def _build_manual_rowspan_map(self, lines, group_field, value_field, agg="sum"):
        """
        Agrupa por bloques CONTIGUOS usando group_field.
        - Si no hay grupo: línea normal (rowspan=1).
        - Si hay grupo: primera línea muestra el valor agregado, resto oculta celda.
        """
        self.ensure_one()
        clean_lines = [l for l in lines if not l.display_type and l.product_type != "combo"]

        out = {}
        i = 0
        while i < len(clean_lines):
            first = clean_lines[i]
            grp = first[group_field]

            if not grp:
                out[first.id] = {"show": True, "rowspan": 1, "value": first[value_field]}
                i += 1
                continue

            j = i
            block = []
            while j < len(clean_lines):
                l = clean_lines[j]
                if l[group_field] and l[group_field].id == grp.id:
                    block.append(l)
                    j += 1
                else:
                    break

            if agg == "sum":
                val = sum(l[value_field] for l in block)
            elif agg == "first":
                val = block[0][value_field]
            elif agg == "weighted_avg":
                qty = sum(l.product_uom_qty for l in block) or 1.0
                val = sum(l[value_field] * l.product_uom_qty for l in block) / qty
            else:
                val = block[0][value_field]

            out[block[0].id] = {"show": True, "rowspan": len(block), "value": val}
            for l in block[1:]:
                out[l.id] = {"show": False, "rowspan": 0, "value": 0.0}

            i = j

        return out

    def _get_manual_report_maps(self, lines):
        self.ensure_one()
        return {
            "subtotal_map": self._build_manual_rowspan_map(
                lines, "unit_group_id", "price_subtotal", agg="sum"
            ),

            "total_map": self._build_manual_rowspan_map(
                lines, "amount_group_id", "price_total", agg="sum"
            ),
        }

    def _compute_tax_totals(self):
        super()._compute_tax_totals()

        for order in self:
            if not order.tax_totals:
                continue

            totals = deepcopy(order.tax_totals)
            changed = False

            # subtotals -> tax_groups
            for subtotal in totals.get("subtotals", []):
                for tg in subtotal.get("tax_groups", []):
                    if tg.get("group_name") == "EXEMPT":
                        tg["group_name"] = "Tax"
                        changed = True
                    if tg.get("tax_group_name") == "EXEMPT":
                        tg["tax_group_name"] = "Tax"
                        changed = True

            # groups_by_subtotal
            for _k, groups in (totals.get("groups_by_subtotal") or {}).items():
                for tg in groups:
                    if tg.get("group_name") == "EXEMPT":
                        tg["group_name"] = "Tax"
                        changed = True
                    if tg.get("tax_group_name") == "EXEMPT":
                        tg["tax_group_name"] = "Tax"
                        changed = True

            if changed:
                order.tax_totals = totals

    @api.depends("amount_total", "currency_id", "partner_id")
    def _compute_amount_total_words(self):
        for order in self:
            if not order.currency_id:
                order.amount_total_words = ""
                continue

            lang = order.partner_id.lang or self.env.user.lang or "en_US"
            total_for_words = order._obvio_round_half_up(order.amount_total, 0)  # 👈 entero con HALF_UP

            try:
                order.amount_total_words = order.currency_id.with_context(lang=lang).amount_to_text(total_for_words)
            except Exception:
                order.amount_total_words = _("%s %.2f") % (order.currency_id.name or "", total_for_words)