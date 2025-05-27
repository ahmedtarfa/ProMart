# -*- coding: utf-8 -*-

# Standard library imports
from datetime import date
import requests  # For making HTTP requests to the forecast API
import logging  # For logging potential issues

# Odoo imports
from odoo import models, fields, api, _  # _ is for translations
from odoo.exceptions import ValidationError, UserError

# Third-party imports
from markupsafe import Markup  # Used to safely render HTML in Odoo fields

# Initialize logger for this module
_logger = logging.getLogger(__name__)

# Define TODAY's date once when the module loads for efficiency
TODAY = date.today()

class MyForecastModel(models.Model):
    """
    Model to handle forecast requests, including date validation and API interaction.
    """
    _name = 'my.forecast.model'
    _description = 'My Forecast Model'

    # == Fields ==
    start_date = fields.Date(
        string='Start Date',
        required=True,
        help="Select the starting date for the forecast period. Must be after today."
    )

    end_date = fields.Date(
        string='End Date',
        required=True,
        help="Select the ending date for the forecast period. Must be after the Start Date."
    )

    forecast_result = fields.Html(
        string="Forecast Result",
        readonly=True,
        copy=False,
        help="Displays the forecast results received from the API."
    )

    # == Constraints ==
    @api.constrains('start_date', 'end_date')
    def _check_dates(self):
        """
        Validation constraint triggered on save.
        Ensures start_date is in the future and end_date is after start_date.
        """
        for record in self:
            if record.start_date and record.start_date <= TODAY:
                raise ValidationError(
                    _("Validation Error: The Start Date must be a future date (after today: %s).") % TODAY.strftime('%Y-%m-%d')
                )

            if record.start_date and record.end_date and record.end_date <= record.start_date:
                raise ValidationError(
                    _("Validation Error: The End Date (%s) must be strictly after the Start Date (%s).") % (
                        record.end_date.strftime('%Y-%m-%d'), record.start_date.strftime('%Y-%m-%d'))
                )

    # == Onchange Methods ==
    @api.onchange('start_date', 'end_date')
    def _onchange_dates(self):
        """
        Provides immediate feedback (warnings) to the user in the form view
        if the selected dates are invalid. Does not prevent saving.
        """
        self.forecast_result = False

        warning = {}
        res = {}

        if self.start_date and self.start_date <= TODAY:
            warning = {
                'title': _("Warning: Invalid Start Date!"),
                'message': _("The Start Date should be a future date (after today: %s).") % TODAY.strftime('%Y-%m-%d')
            }

        elif self.start_date and self.end_date and self.end_date <= self.start_date:
            warning = {
                'title': _("Warning: Invalid Date Range!"),
                'message': _("The End Date (%s) should be strictly after the Start Date (%s).") % (
                    self.end_date.strftime('%Y-%m-%d'), self.start_date.strftime('%Y-%m-%d'))
            }

        if warning:
            res['warning'] = warning

        return res

    # == Actions ==
    def action_forecast(self):
        """
        Button action method.
        Sends selected dates to the external forecast API and displays the result.
        """
        self.ensure_one()

        payload = {
            "start_date": str(self.start_date),
            "end_date": str(self.end_date)
        }

        api_url = "http://11.11.11.17:1111/predict/"
        result_html = ""

        _logger.info(f"Sending forecast request to {api_url} with payload: {payload}")

        try:
            response = requests.post(api_url, json=payload, timeout=60)

            _logger.info(f"Received response from API: Status Code {response.status_code}")

            if response.status_code == 200:
                result_data = response.json()
                _logger.debug(f"API Response Data: {result_data}")

                table_html = """
<div class="table-responsive">
<p>Forecast results from %s to %s:</p>
<table class="table table-sm table-striped table-bordered" style="width: auto; border-collapse: collapse;">
<thead style="background-color: #f0f0f0;">
<tr>
<th style="border: 1px solid #dee2e6; padding: 5px 8px; text-align: left;">Date</th>
<th style="border: 1px solid #dee2e6; padding: 5px 8px; text-align: right;">Forecasted Sales</th>
</tr>
</thead>
<tbody>
""" % (self.start_date.strftime('%Y-%m-%d'), self.end_date.strftime('%Y-%m-%d'))

                if isinstance(result_data, list) and result_data:
                    for entry in result_data:
                        date_str = entry.get('ds', 'N/A')
                        if isinstance(date_str, str) and 'T' in date_str:
                            date_str = date_str.split('T')[0]

                        forecast_val = entry.get('yhat', 0.0)

                        table_html += f"""
<tr>
<td style="border: 1px solid #dee2e6; padding: 5px 8px;">{date_str}</td>
<td style="border: 1px solid #dee2e6; padding: 5px 8px; text-align: right;">{forecast_val:.2f}</td>
</tr>
"""
                elif isinstance(result_data, list) and not result_data:
                    table_html += '<tr><td colspan="2" style="border: 1px solid #dee2e6; padding: 8px; text-align: center;">API returned an empty forecast list.</td></tr>'
                else:
                    _logger.warning(f"Unexpected data format received from API: {type(result_data)}")
                    table_html += '<tr><td colspan="2" style="border: 1px solid #dee2e6; padding: 8px; text-align: center;">Unexpected data format received from API.</td></tr>'

                table_html += """
</tbody>
</table>
</div>
"""
                result_html = Markup(table_html)

            else:
                error_message = f"<p class='alert alert-warning'>API Error: Received status code {response.status_code}.</p>"
                try:
                    error_details = response.text
                    error_message += f"<pre>{Markup.escape(error_details)}</pre>"
                    _logger.error(f"API Error {response.status_code}: {error_details}")
                except Exception as e:
                    _logger.error(f"Could not read API error response body: {e}")

                result_html = Markup(error_message)

        except requests.exceptions.Timeout:
            _logger.error(f"API request timed out after 60 seconds: {api_url}")
            result_html = Markup(
                "<p class='alert alert-danger'>Request Failed: The request to the forecast API timed out. The API might be slow or unavailable.</p>"
            )
        except requests.exceptions.RequestException as e:
            _logger.error(f"API Request Failed: {e}")
            result_html = Markup(
                f"<p class='alert alert-danger'>Request Failed: Could not connect to the forecast API ({api_url}). Please check the API server and network connection.<br/>Details: {Markup.escape(str(e))}</p>"
            )
        except Exception as e:
            _logger.exception("An unexpected error occurred during forecasting.")
            result_html = Markup(
                f"<p class='alert alert-danger'>An unexpected error occurred: {Markup.escape(str(e))}</p>"
            )

        self.write({'forecast_result': result_html})
        return True
