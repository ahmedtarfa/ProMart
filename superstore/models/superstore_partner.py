from odoo import models, fields

class SuperstorePartner(models.Model):
    _inherit = "res.partner"

    order_ids = fields.One2many('sale.order', 'partner_id', string="Orders")
    x_segement = fields.Selection([
        ('consumer', 'Consumer'),
        ('corporate', 'Corporate'),
        ('home_office', 'Home Office')
    ], string="segment")
    x_region = fields.Char(string="region", required=True)