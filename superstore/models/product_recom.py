from odoo import models, fields, api
import requests

class MyRecomModel(models.Model):
    _name = 'my.recom.model'
    _description = 'My Recommndtion Model'

    user_id = fields.Text()
    recom_result = fields.Text(string="Products Recommended", readonly=True)

    def action_recom(self):
        for record in self:
            # Prepare payload for your FastAPI service
            payload = {
                "user_id": str(record.user_id),
            }

            try:
                # Replace with your actual FastAPI URL
                response = requests.post("http://192.168.0.107:1113/predict", json=payload)
                if response.status_code == 200:
                    result = response.json()
                    recom_lines = [f"{entry['product_id']}" for entry in result]
                    record.recom_result = "\n".join(recom_lines)
                else:
                    record.recom_result = f"API Error: {response.status_code}"
            except Exception as e:
                record.recom_result = f"Request failed: {str(e)}"
