from odoo import models, fields

class SuperstoreProduct(models.Model):
    _inherit = "product.template"

    x_productid=fields.Char(string="Product ID", required=False, default='N/A')
    x_sub_category=fields.Char(string='Sub Category2', required=False, default='N/A')