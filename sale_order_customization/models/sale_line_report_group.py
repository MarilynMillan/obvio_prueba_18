# -*- coding: utf-8 -*-
from odoo import api, fields, models


class SaleOrderLineReportGroup(models.Model):
    _name = "sale.order.line.report.group"
    _description = "SO Line Report Group"
    _order = "group_type, sequence, id"

    name = fields.Char(required=True)
    order_id = fields.Many2one("sale.order", required=True, ondelete="cascade", index=True)
    group_type = fields.Selection(
        [("unit", "Unit Price"), ("amount", "Amount")],
        required=True,
        index=True,
    )
    sequence = fields.Integer(default=10)

    _sql_constraints = [
        (
            "uniq_so_group_type_name",
            "unique(order_id, group_type, name)",
            "Group name must be unique per order and type.",
        ),
    ]

class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    unit_group_id = fields.Many2one(
        "sale.order.line.report.group",
        string="Unit Group",
        domain="[('order_id','=',order_id), ('group_type','=','unit')]",
        copy=False,
    )
    amount_group_id = fields.Many2one(
        "sale.order.line.report.group",
        string="Amount Group",
        domain="[('order_id','=',order_id), ('group_type','=','amount')]",
        copy=False,
    )
