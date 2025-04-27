from markupsafe import Markup
from odoo import models, fields, api
import requests

class MyForecastModel(models.Model):
    _name = 'my.forecast.model'
    _description = 'My Forecast Model'

    start_date = fields.Date()
    end_date = fields.Date()
    forecast_result = fields.Text(string="Forecast Result", readonly=True)


    def action_forecast(self):
        for record in self:
            # Prepare payload for your FastAPI service
            payload = {
                "start_date": str(record.start_date),
                "end_date": str(record.end_date)
            }

            try:
                # Replace with your actual FastAPI URL
                response = requests.post("http://192.168.1.10:1111/predict", json=payload)
                if response.status_code == 200:
                    result = response.json()
                    forecast_lines = [f"{entry['ds']}: {entry['yhat']:.2f}" for entry in result]
                    record.forecast_result = "\n".join(forecast_lines)
                else:
                    record.forecast_result = f"API Error: {response.status_code}"
            except Exception as e:
                record.forecast_result = f"Request failed: {str(e)}"
