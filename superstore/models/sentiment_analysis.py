from odoo import models, fields, api
import requests

class NySentimentAnalysis(models.Model):
    _name = 'my.sent.model'
    _description = 'My Sentiment Analysis'

    review = fields.Text()
    rate = fields.Text(string="Review Rate", readonly=True)

    def action_sent(self):
        for record in self:
            # Split reviews by newline
            reviews_list = [line.strip() for line in str(record.review).split('\n') if line.strip()]

            payload = {
                "reviews": reviews_list  # ✅ send multiple reviews
            }

            try:
                response = requests.post("http://11.11.11.17:1113/predict/", json=payload)
                if response.status_code == 200:
                    result = response.json()
                    # Format each review with its corresponding rate
                    sent_lines = [f"{entry['review']} => (({entry['rate']}))" for entry in result]
                    record.rate = "\n".join(sent_lines)
                else:
                    record.rate = f"API Error: {response.status_code}"
            except Exception as e:
                record.rate = f"Request failed: {str(e)}"
