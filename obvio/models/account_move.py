from odoo import api, fields, models, _

class AccountMove(models.Model):
    _inherit = 'account.move'

    # Moneda USD fija
    currency_usd_id = fields.Many2one(
        'res.currency',
        string='USD Currency',
        compute='_compute_currency_usd',
        store=True
    )

    # Monto en USD (moneda fija)
    amount_untaxed_usd = fields.Monetary(
        string='Total(USD)',
        currency_field='currency_usd_id',
        compute='_compute_amount_untaxed_usd',
        store=True
    )

    @api.depends('company_id')
    def _compute_currency_usd(self):
        usd_currency = self.env.ref('base.USD', raise_if_not_found=False)
        for move in self:
            move.currency_usd_id = usd_currency.id if usd_currency else False

    @api.depends(
        'currency_id',
        'amount_untaxed_in_currency_signed',
        'invoice_currency_rate',
        'move_type'
    )
    def _compute_amount_untaxed_usd(self):
        usd_currency = self.env.ref('base.USD', raise_if_not_found=False)

        for move in self:
            move.amount_untaxed_usd = 0.0

            if not usd_currency:
                continue

            # Si la factura ya está en USD
            if move.currency_id == usd_currency:
                move.amount_untaxed_usd = move.amount_total
                continue

            # Si la moneda es distinta de USD
            if move.invoice_currency_rate and move.invoice_currency_rate != 0:
                move.amount_untaxed_usd = (
                    move.amount_total / move.invoice_currency_rate
                )