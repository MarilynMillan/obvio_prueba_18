from odoo import api, fields, models, _
from odoo.exceptions import ValidationError
from odoo.tools.float_utils import float_is_zero

class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    market_id = fields.Many2one("project.zone", string="Market")

    location_id = fields.Many2one(
        "zone.ubication",
        string="Location",
        domain="[('zone_id', '=', market_id)]",
    )

    operator_id = fields.Many2one(
        "res.partner",
        string="Operator",
        domain="[('is_operator', '=', True)]",
    )

    store_id = fields.Many2one(
        "zone.tienda",
        string="Store",
        domain="[('ubication_id', '=', location_id)]",
    )

    brand_id = fields.Many2one(
        "sale.brand",
        string="Brand",
        check_company=True,
        domain="[('company_id', 'in', [False, company_id])]",
    )

    qty_print = fields.Char(compute="_compute_qty_print")

    def action_autofill_lines_from_project(self):
        orders = self.mapped("order_id")
        return orders.action_autofill_lines_from_project()

    @api.depends("product_uom_qty")
    def _compute_qty_print(self):
        for l in self:
            q = l.product_uom_qty or 0.0
            if float(q).is_integer():
                l.qty_print = str(int(q))
            else:
                l.qty_print = ("%s" % q).rstrip("0").rstrip(".")

    @api.constrains("brand_id", "market_id", "location_id", "operator_id", "store_id", "company_id")
    def _check_company_consistency(self):
        for line in self:
            for field_name in ["brand_id", "market_id", "location_id", "operator_id", "store_id"]:
                rec = line[field_name]
                if not rec:
                    continue

                if "company_id" in rec._fields and rec.company_id and line.company_id and rec.company_id != line.company_id:
                    raise ValidationError(_(
                        "The selected value for '%(field)s' belongs to company '%(rec_company)s', "
                        "but this sales order line belongs to '%(line_company)s'."
                    ) % {
                        "field": line._fields[field_name].string,
                        "rec_company": rec.company_id.display_name,
                        "line_company": line.company_id.display_name,
                    })

            if line.location_id and line.market_id and line.location_id.zone_id != line.market_id:
                raise ValidationError(_(
                    "The selected Location '%(location)s' does not belong to Market '%(market)s'."
                ) % {
                    "location": line.location_id.display_name,
                    "market": line.market_id.display_name,
                })

            if line.store_id and line.location_id and line.store_id.ubication_id != line.location_id:
                raise ValidationError(_(
                    "The selected Store '%(store)s' does not belong to Location '%(location)s'."
                ) % {
                    "store": line.store_id.display_name,
                    "location": line.location_id.display_name,
                })
