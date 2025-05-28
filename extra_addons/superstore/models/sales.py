from odoo import models, fields

class SuperstoreSaleOrder(models.Model):
    _inherit = "sale.order"

    x_orderid = fields.Char(
        string="Order ID",
        required=True,
        copy=False,
        readonly=True,
        default=lambda self: self.env['ir.sequence'].next_by_code('sale.order.custom')
    )
    x_discount = fields.Float(string="Discount")
    x_profit = fields.Float(string="Profit")
    x_rate = fields.Integer(string="Rate")
    x_review = fields.Text(string="Review")
    x_shipmode = fields.Selection([
        ('standard_class', 'Standard Class'),
        ('second_class', 'Second Class'),
        ('first_class', 'First Class'),
        ('same_day', 'Same Day'),
    ], string="Ship Mode")
    x_shipdate = fields.Date(string="Ship Date")
    partner_id = fields.Many2one('res.partner', string="Customer")
