from odoo import models, fields, api
import requests
import json
import logging

_logger = logging.getLogger(__name__)

class MyRecomModel(models.Model):
    _name = 'my.recom.user.model'
    _description = 'Recommendation based on Customer Reference (Personalized or Top Selling)'

    user_id = fields.Many2one('res.users', string="User", required=True)
    user_recom_result = fields.Text(string="Recommended Products", readonly=True)

    @api.model
    def action_user_recom(self):
        for record in self:
            partner = record.user_id.partner_id
            customer_reference = partner.ref if partner else None
            _logger.info(f"Fetching recommendations for user: {record.user_id.id} with customer_reference: {customer_reference}")

            result = self.get_recommendation_from_api(customer_reference)
            if isinstance(result, list):
                result_details = self.format_recommendations(result)
                record.user_recom_result = json.dumps(result_details, ensure_ascii=False, indent=4)
                _logger.info(f"Recommendations fetched and formatted for user {record.user_id.id}: {result_details}")
            else:
                record.user_recom_result = result
                _logger.error(f"Error fetching recommendations for user {record.user_id.id}: {result}")

    def get_recommendation_from_api(self, customer_reference):
        """Function to get recommendations based on Customer Reference or return top sellers."""
        payload = {"customer_id": customer_reference}

        try:
            response = requests.post("http://11.11.11.17:1115/recommend_by_user", json=payload)
            response.raise_for_status()  # Raise HTTPError for bad responses (4xx or 5xx)
            result = response.json()
            return result.get("recommendations", [])
        except requests.exceptions.RequestException as e:
            error_message = f"Request failed: {str(e)}"
            _logger.error(error_message)
            return error_message
        except json.JSONDecodeError:
            error_message = "Error decoding JSON response from API."
            _logger.error(error_message)
            return error_message

    def format_recommendations(self, recommendations):
        """Helper function to format recommendations data."""
        formatted_data = []
        for product in recommendations:
            formatted_data.append({
                'product_name': product.get('product_name', ''),
                'product_description': product.get('product_description', ''),
                'price': product.get('price', ''),
                'rate': product.get('rate', ''),
                'category': product.get('category', ''),
                'image_url': product.get('image_url', ''),
                'id': product.get('id', ''),
            })
        return formatted_data