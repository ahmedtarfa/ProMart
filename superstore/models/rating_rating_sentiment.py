from odoo import models, fields, api
import requests

class RatingRating(models.Model):
    _inherit = 'rating.rating'  # Extending the original model

    sentiment_result = fields.Text(string="Sentiment Analysis", compute='_compute_sentiment_result', store=True)

    @api.depends('feedback')  # Assuming 'feedback' is the review text field
    def _compute_sentiment_result(self):
        for record in self:
            if record.feedback:
                payload = {
                    "reviews": [record.feedback]
                }
                try:
                    response = requests.post("http://11.11.11.17:1113/predict/", json=payload)
                    if response.status_code == 200:
                        result = response.json()
                        if result:
                            entry = result[0]
                            record.sentiment_result = f"{entry['review']} => (({entry['rate']}))"
                        else:
                            record.sentiment_result = "No result"
                    else:
                        record.sentiment_result = f"API Error: {response.status_code}"
                except Exception as e:
                    record.sentiment_result = f"Request failed: {str(e)}"
            else:
                record.sentiment_result = "No feedback"
