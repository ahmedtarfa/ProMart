from odoo import http
from odoo.http import request
import requests
import json
import os
from dotenv import load_dotenv
load_dotenv()
ip = os.getenv("IP")

class SuperstoreRecommendation(http.Controller):

    @http.route('/recommend', type='http', auth='public', website=True)
    def recommendation_page(self, **kwargs):
        search_query = kwargs.get('query')
        grouped_products = {}
        error = None
        is_logged_in = False  # التحقق مما إذا كان المستخدم مسجلاً
        is_new_customer = False  # العميل جديد
        is_existing_customer = False  # العميل قديم

        try:
            ProductTemplate = request.env['product.template'].sudo()
            user_id = request.session.uid
            customer_reference = None
            added_product_ids = set()  # 🛡 تجنب التكرار

            if user_id:
                partner = request.env['res.users'].sudo().browse(user_id).partner_id
                customer_reference = partner and partner.ref
                is_logged_in = True  # إذا كان المستخدم مسجلاً، قم بتعيين هذا المتغير كـ True

                # 🔍 تحديد إذا كان عميل جديد أو قديم بناءً على سجل الطلبات
                sale_orders = request.env['sale.order'].sudo().search([('partner_id', '=', partner.id)], limit=1)
                if sale_orders:
                    is_existing_customer = True
                else:
                    is_new_customer = True

            if search_query:
                # 🔍 بحث بالكلمة المفتاحية
                search_url = f"http://{ip}:1114/predict"
                headers = {'Content-Type': 'application/json'}
                payload = json.dumps({"query": search_query})

                response = requests.post(search_url, headers=headers, data=payload)
                response.raise_for_status()

                search_results = response.json().get('recommendations', [])

                for result in search_results:
                    product_name = result.get('Product Name')
                    metadata = result.get('metadata', {})
                    product_id = metadata.get('Product ID')
                    yahoo_image_url = result.get('Yahoo Image URL', 'Not found')

                    product = ProductTemplate.search([('default_code', '=', product_id)], limit=1)
                    if not product or product.id in added_product_ids:
                        continue

                    image = product.image_1920 and f'/web/image?model=product.template&id={product.id}&field=image_1920' or yahoo_image_url

                    product_data = {
                        'product_name': product_name,
                        'product_description': metadata.get('Product Description', ''),
                        'price': product.list_price,
                        'image_1920': image,
                        'product_id': product.id,
                    }

                    grouped_products.setdefault('search_results', []).append(product_data)
                    added_product_ids.add(product.id)

            else:
                # ✅ إحضار التوصيات بناء على العميل أو المنتجات الرائجة
                if customer_reference:
                    recommend_url = f"http://{ip}:1115/recommend_by_user"
                    headers = {'Content-Type': 'application/json'}
                    payload = json.dumps({"customer_id": customer_reference})

                    response = requests.post(recommend_url, headers=headers, data=payload)
                    response.raise_for_status()
                    response_json = response.json()

                    recommendations_data = response_json.get('recommendations', [])
                    if isinstance(recommendations_data, dict):
                        grouped_products = self._process_grouped_recommendations_dict(recommendations_data)
                    else:
                        grouped_products = self._process_grouped_recommendations(recommendations_data)
                else:
                    recommend_url = f"http://{ip}:1115/high_sales_product_recommendation"
                    response = requests.get(recommend_url)
                    response.raise_for_status()
                    response_json = response.json()
                    grouped_products = self._process_grouped_recommendations_dict(response_json.get('recommendations', {}))

        except Exception as e:
            error = str(e)

        return request.render('superstore.recommendation_template', {
            'search_query': search_query,
            'grouped_products': grouped_products,
            'error': error,
            'is_logged_in': is_logged_in,
            'is_new_customer': is_new_customer,
            'is_existing_customer': is_existing_customer,
        })

    def _process_grouped_recommendations(self, recommendations):
        """🔄 معالجة التوصيات (قائمة) مع عرض فقط الفئات الأساسية."""
        ProductTemplate = request.env['product.template'].sudo()
        grouped = {}
        allowed_categories = {'Furniture', 'Office Supplies', 'Technology'}
        added_ids = set()

        for rec in recommendations:
            internal_ref = rec.get('id')
            product = ProductTemplate.search([('default_code', '=', internal_ref)], limit=1)
            if product and product.id not in added_ids:
                image = product.image_1920 and f'/web/image?model=product.template&id={product.id}&field=image_1920' or rec.get('image_url')
                product_data = {
                    'product_name': rec.get('product_name'),
                    'product_description': rec.get('product_description'),
                    'price': product.list_price,
                    'image_1920': image,
                    'product_id': product.id,
                }
                for category in product.public_categ_ids:
                    if category.name in allowed_categories:
                        key = (category.id, category.name)
                        grouped.setdefault(key, []).append(product_data)
                        added_ids.add(product.id)
                        break
        return grouped

    def _process_grouped_recommendations_dict(self, grouped_dict):
        """🔄 معالجة التوصيات (قاموس) مع عرض فقط الفئات الأساسية."""
        ProductTemplate = request.env['product.template'].sudo()
        grouped = {}
        allowed_categories = {'Furniture', 'Office Supplies', 'Technology'}
        added_ids = set()

        for category_name, products in grouped_dict.items():
            for rec in products:
                internal_ref = rec.get('id')
                product = ProductTemplate.search([('default_code', '=', internal_ref)], limit=1)
                if product and product.id not in added_ids:
                    image = product.image_1920 and f'/web/image?model=product.template&id={product.id}&field=image_1920' or rec.get('image_url')
                    for category in product.public_categ_ids:
                        if category.name in allowed_categories:
                            key = (category.id, category.name)
                            grouped.setdefault(key, []).append({
                                'product_name': rec.get('product_name'),
                                'product_description': rec.get('product_description'),
                                'price': product.list_price,
                                'image_1920': image,
                                'product_id': product.id,
                            })
                            added_ids.add(product.id)
                            break
        return grouped
