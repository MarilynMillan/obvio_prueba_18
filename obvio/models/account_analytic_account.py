from odoo import api, fields, models, _

class AccountAnalyticAccount(models.Model):
    _inherit = 'account.analytic.account'

    margin_percent = fields.Float(string="Margin %", compute="_compute_margin_percent", digits=(16, 2))


    def _compute_margin_percent(self):
        for rec in self:
            if rec.credit:
                rec.margin_percent = ((rec.credit - rec.debit) / rec.credit) * 100
            else: 
                rec.margin_percent = 0.0
