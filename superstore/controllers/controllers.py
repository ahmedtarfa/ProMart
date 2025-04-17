# -*- coding: utf-8 -*-
# from odoo import http


# class Superstore(http.Controller):
#     @http.route('/superstore/superstore', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/superstore/superstore/objects', auth='public')
#     def list(self, **kw):
#         return http.request.render('superstore.listing', {
#             'root': '/superstore/superstore',
#             'objects': http.request.env['superstore.superstore'].search([]),
#         })

#     @http.route('/superstore/superstore/objects/<model("superstore.superstore"):obj>', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('superstore.object', {
#             'object': obj
#         })

