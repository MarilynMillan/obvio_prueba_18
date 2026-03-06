# -*- coding: utf-8 -*-
from odoo import api, fields, models
from datetime import date
import calendar
from dateutil.relativedelta import relativedelta


class IrSequence(models.Model):
    _inherit = "ir.sequence"

    @api.model
    def _obvio_month_bounds(self, d):
        d = fields.Date.to_date(d)
        date_from = date(d.year, d.month, 1)
        last_day = calendar.monthrange(d.year, d.month)[1]
        date_to = date(d.year, d.month, last_day)
        return date_from, date_to

    @api.model
    def _obvio_is_month_range(self, dr):
        """True if dr is exactly a full calendar month."""
        if not dr.date_from or not dr.date_to:
            return False
        if dr.date_from.day != 1:
            return False
        last_day = calendar.monthrange(dr.date_from.year, dr.date_from.month)[1]
        return dr.date_to == date(dr.date_from.year, dr.date_from.month, last_day)

    @api.model
    def _obvio_delete_annual_ranges(self, seq, years):
        """Remove annual ranges (Jan 1 -> Dec 31) that can shadow monthly ranges."""
        DR = self.env["ir.sequence.date_range"].sudo()
        for y in years:
            annual = DR.search([
                ("sequence_id", "=", seq.id),
                ("date_from", "=", date(y, 1, 1)),
                ("date_to", "=", date(y, 12, 31)),
            ])
            if annual:
                annual.unlink()

    @api.model
    def _obvio_delete_overlapping_non_month_ranges(self, seq, months):
        """
        If there are overlapping ranges (fiscal-year, yearly, custom),
        they can break range_month. Remove any overlapping non-month ranges.
        """
        DR = self.env["ir.sequence.date_range"].sudo()
        for m in months:
            df, dt = self._obvio_month_bounds(m)
            overlaps = DR.search([
                ("sequence_id", "=", seq.id),
                ("date_from", "<=", dt),
                ("date_to", ">=", df),
            ], order="id asc")
            bad = overlaps.filtered(lambda r: not self._obvio_is_month_range(r))
            if bad:
                bad.unlink()

    @api.model
    def _obvio_ensure_ranges_for_months(self, seq, months):
        """Ensure monthly date ranges exist for given month anchor dates."""
        DR = self.env["ir.sequence.date_range"].sudo()
        for m in months:
            df, dt = self._obvio_month_bounds(m)
            exists = DR.search([
                ("sequence_id", "=", seq.id),
                ("date_from", "=", df),
                ("date_to", "=", dt),
            ], limit=1)
            if not exists:
                DR.create({
                    "sequence_id": seq.id,
                    "date_from": df,
                    "date_to": dt,
                    "number_next": 1,
                })

    @api.model
    def _obvio_get_template_sequence(self, code):
        Sequence = self.sudo()
        # Prefer template (company_id False)
        template = Sequence.search([("code", "=", code), ("company_id", "=", False), ("active", "=", True)], limit=1)
        if not template:
            # fallback: any active
            template = Sequence.search([("code", "=", code), ("active", "=", True)], limit=1)
        return template

    @api.model
    def _obvio_get_or_create_company_sequence(self, template_seq, company):
        """
        Ensure a company-specific sequence exists for the same code.
        This keeps counters independent per company.
        """
        seq = self.sudo().search([
            ("code", "=", template_seq.code),
            ("company_id", "=", company.id),
            ("active", "=", True),
        ], limit=1)

        if not seq:
            seq = template_seq.sudo().copy({
                "name": f"{template_seq.name} ({company.display_name})",
                "company_id": company.id,
                "number_next": 1,
            })

        # Enforce correct settings
        seq.sudo().write({
            "use_date_range": True,
            "prefix": "%(range_year)s.%(range_month)s-",
        })
        return seq

    @api.model
    def cron_obvio_ensure_sale_order_quote_ranges(self):
        SEQ_CODE = "sale.order.obvio.quote"

        # Mes actual + siguiente
        today = fields.Date.context_today(self)
        next_month = (fields.Date.to_date(today) + relativedelta(months=1))
        months = [today, next_month]
        years = {fields.Date.to_date(m).year for m in months}

        # Agarra TEMPLATE (company_id False) si existe, si no, cualquier seq
        template = self.sudo().search([
            ("code", "=", SEQ_CODE),
            ("company_id", "=", False),
            ("active", "=", True),
        ], limit=1) or self.sudo().search([
            ("code", "=", SEQ_CODE),
            ("active", "=", True),
        ], limit=1)

        if not template:
            return True

        # Asegura que template esté bien configurada
        template.sudo().write({
            "use_date_range": True,
            "prefix": "%(range_year)s.%(range_month)s-",
        })

        # LIMPIAR TEMPLATE
        self._obvio_delete_annual_ranges(template, years)
        self._obvio_delete_overlapping_non_month_ranges(template, months)
        self._obvio_ensure_ranges_for_months(template, months)

        # Para cada compañía: asegurar su secuencia y sus rangos mensuales
        companies = self.env["res.company"].sudo().search([])
        for company in companies:
            seq = self._obvio_get_or_create_company_sequence(template, company)

            # Limpieza + asegurar rangos mensuales
            self._obvio_delete_annual_ranges(seq, years)
            self._obvio_delete_overlapping_non_month_ranges(seq, months)
            self._obvio_ensure_ranges_for_months(seq, months)

        return True