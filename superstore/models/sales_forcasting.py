from markupsafe import Markup
from odoo import models, fields, api
import requests

class MyModel(models.Model):
    _name = 'my.model'
    _description = 'My Model'

    name = fields.Char()
    description = fields.Text()
    start_date = fields.Date()
    end_date = fields.Date()
    forecast_result = fields.Text(string="Forecast Result", readonly=True)
    chat = fields.Html(string='chat', sanitize=False, compute='rag_ai_chat')



    # def rag_ai_chat(self):
    #     for record in self:
    #         html = ['<div class="chat-container">']
    #         for msg in record.chat_history:
    #             if msg.user:
    #                 html.append(f'''<div class="message_user">
    #                                    <div class="message_content">{msg.user}</div>
    #                                     </div>'''
    #                             )
    #             if msg.ai:
    #                 html.append(f'''<div class="message_ai">
    #                                    <div class="message_content">{msg.ai}</div>
    #                                     </div> ''')
    #
    #         html.append('</div>')
    #         record.chat = Markup(''.join(html))



    def action_forecast(self):
        for record in self:
            # Prepare payload for your FastAPI service
            payload = {
                "start_date": str(record.start_date),
                "end_date": str(record.end_date)
            }

            try:
                # Replace with your actual FastAPI URL
                response = requests.post("http://11.11.11.20:1111/predict", json=payload)
                if response.status_code == 200:
                    result = response.json()
                    forecast_lines = [f"{entry['ds']}: {entry['yhat']:.2f}" for entry in result]
                    record.forecast_result = "\n".join(forecast_lines)
                else:
                    record.forecast_result = f"API Error: {response.status_code}"
            except Exception as e:
                record.forecast_result = f"Request failed: {str(e)}"


    # class ChatHistory(models.Model):
    #     _name = "chat.history"
    #
    #     user = fields.Char(string='User')
    #     ai = fields.Char(string='AI')