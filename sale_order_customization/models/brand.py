# models/brand.py
from odoo import api, fields, models

class SaleBrand(models.Model):
    _name = "sale.brand"
    _description = "Sales Brand"
    _order = "name"

    name = fields.Char(required=True, index=True)
    active = fields.Boolean(default=True)
    company_id = fields.Many2one("res.company", default=lambda self: self.env.company)

    _sql_constraints = [
        ("name_company_uniq", "unique(name, company_id)", "Brand must be unique per company."),
    ]
