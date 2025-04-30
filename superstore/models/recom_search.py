from odoo import models, fields
import requests

class MySearchRecomModel(models.Model):
    _name = 'my.recom.search.model'
    _description = 'My Recommendation by Search Model'

    search_text = fields.Text()
    search_recom_result = fields.Text(string="Products Recommended From Search", readonly=True)

    def action_search_recom(self):
        for record in self:
            result = self.get_recommendation_from_api(record.search_text)
            record.search_recom_result = str(result) if not isinstance(result, str) else result # Store raw result (or error)

    def get_recommendation_from_api(self, query):
        """Function to be used by controller and button"""
        payload = {"query": str(query)}

        try:
            response = requests.post("http://192.168.1.90:1114/predict", json=payload)
            #response = requests.post("https://e8b8-2c0f-fc88-5-9b9d-e092-51df-6350-c502.ngrok-free.app/predict",json=payload)
            if response.status_code == 200:
                result = response.json()
                return result.get("recommendations", [])
            else:
                return f"API Error: {response.status_code}"
        except Exception as e:
            return f"Request failed: {str(e)}"