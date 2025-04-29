from odoo import models, fields, api
import requests
import json

class MyRecomModel(models.Model):
    _name = 'my.recom.user.model'
    _description = 'My Recommendation based on Customer Reference'

    user_id = fields.Many2one('res.users', string="User", required=True)
    user_recom_result = fields.Text(string="Products Recommended Based on User", readonly=True)

    @api.model
    def action_user_recom(self):
        for record in self:
            partner = record.user_id.partner_id
            customer_reference = partner.ref  # استخدام .ref بدل .reference

            if not customer_reference:
                record.user_recom_result = "No customer reference found for this user."
                continue

            result = self.get_recommendation_from_api(customer_reference)
            if isinstance(result, list):
                # Store the recommendation details in a readable format
                result_details = self.format_recommendations(result)
                record.user_recom_result = json.dumps(result_details, ensure_ascii=False, indent=4)
            else:
                record.user_recom_result = result  # Error message if something went wrong

    def get_recommendation_from_api(self, customer_reference):
        """Function to get recommendations based on Customer Reference"""
        payload = {"customer_id": customer_reference}

        try:
            response = requests.post("http://192.168.1.90:1115/recommend_by_user", json=payload)
            if response.status_code == 200:
                result = response.json()
                return result.get("recommendations", [])
            else:
                return f"API Error: {response.status_code}"
        except Exception as e:
            return f"Request failed: {str(e)}"

    def get_high_rate_recommendations(self):
        """Function to get high rate products if customer is not logged in"""
        try:
            response = requests.get("http://192.168.1.90:1115/high_rate_recommendations")
            if response.status_code == 200:
                result = response.json()

                category_products = {}

                for item in result.get("recommendations", []):
                    # تحقق من وجود تقييم 3 أو أعلى
                    if item.get('Rate', 0) < 3:
                        continue  # استبعاد المنتجات التي تقييمها أقل من 3

                    # تحقق من القيم الغير صالحة في السعر
                    if isinstance(item.get('price'), float) and (item['price'] != item['price']):  # Check if NaN
                        continue  # استبعاد المنتج الذي يحتوي على سعر غير صالح (NaN)
                    
                    # تحقق من وجود صورة
                    if not item.get('Yahoo Image URL'):
                        continue  # استبعاد المنتج الذي لا يحتوي على صورة صالحة

                    # إضافة المنتج إلى قائمة الفئة
                    category = item.get('Category', 'Uncategorized')
                    if category not in category_products:
                        category_products[category] = []
                    category_products[category].append(item)

                # تحديد فقط 5 منتجات لكل فئة
                top_products_per_category = {}
                for category, products in category_products.items():
                    # ترتيب المنتجات حسب التقييم (من الأعلى إلى الأدنى)
                    sorted_products = sorted(products, key=lambda x: x['Rate'], reverse=True)
                    top_products_per_category[category] = sorted_products[:5]  # أخذ أول 5 منتجات

                return top_products_per_category
            else:
                return f"API Error: {response.status_code}"
        except Exception as e:
            return f"Request failed: {str(e)}"

    def format_recommendations(self, recommendations):
        """Helper function to format recommendations data"""
        formatted_data = []
        for product in recommendations:
            formatted_data.append({
                'product_name': product.get('Product Name', ''),
                'product_description': product.get('Product Description', ''),
                'price': product.get('price', ''),
                'rate': product.get('Rate', ''),
                'category': product.get('Category', ''),
                'image_url': product.get('Yahoo Image URL', ''),
            })
        return formatted_data