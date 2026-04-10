from odoo import api, fields, models, _

class AccountMove(models.Model):
    _inherit = 'account.move'

    
    currency_usd_id = fields.Many2one(
        'res.currency',
        string='USD Currency',
        compute='_compute_currency_usd',
        help="Moneda de referencia USD para cálculos internos."
    )

    amount_untaxed_usd = fields.Monetary(
        string='Total(USD)',
        currency_field='currency_usd_id',
        compute='_compute_amount_untaxed_usd',
        help="Monto total convertido a USD basado en la tasa de la factura."
    )

    @api.depends('company_id')
    def _compute_currency_usd(self):
        """Busca la moneda USD una sola vez para mejorar el rendimiento."""
        usd_currency = self.env.ref('base.USD', raise_if_not_found=False)
        if not usd_currency:
            usd_currency = self.env['res.currency'].search([('name', '=', 'USD')], limit=1)
        
        for move in self:
            move.currency_usd_id = usd_currency.id if usd_currency else False

    @api.depends('currency_id', 'amount_total', 'invoice_currency_rate', 'move_type')
    def _compute_amount_untaxed_usd(self):
        """Calcula el total en USD manejando signos para facturas y notas de crédito."""
        for move in self:
            val_usd = 0.0
            
            # 1. Verificación de seguridad: moneda USD y monto base
            if move.currency_usd_id and move.amount_total:
                amount_base = move.amount_total
                
                # 2. Conversión según la moneda de la factura
                if move.currency_id == move.currency_usd_id:
                    val_usd = amount_base
                elif move.invoice_currency_rate and move.invoice_currency_rate != 0:
                    # Usamos la tasa guardada en la factura
                    val_usd = amount_base / move.invoice_currency_rate
                
                # 3. LÓGICA DE SIGNOS UNIFICADA (CLIENTES Y PROVEEDORES)
                # out_refund = Nota Crédito Cliente
                # in_refund = Nota Crédito Proveedor
                if move.move_type in ('out_refund', 'in_refund'):
                    # Forzamos negativo para cualquier tipo de reembolso/crédito
                    move.amount_untaxed_usd = -abs(val_usd)
                else:
                    # Positivo para facturas normales (out_invoice, in_invoice)
                    move.amount_untaxed_usd = abs(val_usd)
            else:
                # Si no hay datos suficientes, devolvemos cero
                move.amount_untaxed_usd = 0.0