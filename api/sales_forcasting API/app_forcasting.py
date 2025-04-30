import uvicorn
from fastapi import FastAPI
from pydantic import BaseModel
from datetime import datetime , timedelta
import pandas as pd
import numpy as np
import joblib
from prophet import Prophet
from scipy.special import inv_boxcox
from typing import List
import os

app = FastAPI()

# Load the Prophet model and transformers
base_path = os.path.dirname(os.path.abspath(__file__))

# Load the files using full paths
model = joblib.load(os.path.join(base_path, "prophet_model.pkl"))
scaler = joblib.load(os.path.join(base_path, "scaler.pkl"))
boxcox_lambda = joblib.load(os.path.join(base_path, "boxcox_lambda.pkl"))

# Input schema
class ModelInput(BaseModel):
    start_date: str
    end_date: str

# Output schema
class ForecastOutput(BaseModel):
    ds: datetime
    yhat: float

@app.post("/predict/", response_model=List[ForecastOutput])
def predict_sales(date: ModelInput):
    start = datetime.strptime(date.start_date, "%Y-%m-%d") - timedelta(days=1)
    end = datetime.strptime(date.end_date, "%Y-%m-%d")

    future_df = pd.DataFrame({'ds': pd.date_range(start=start, end=end, freq='D')})
    future_df['month_year'] = future_df['ds'].dt.year * 100 + future_df['ds'].dt.month

    forecast = model.predict(future_df)

    forecast['yhat_scaled_inv'] = scaler.inverse_transform(forecast[['yhat']])
    forecast['yhat_scaled_box'] = inv_boxcox(forecast['yhat_scaled_inv'], boxcox_lambda)

    forecast['yhat_final'] = forecast['yhat_scaled_box'].diff()
    forecast['yhat_final'] = forecast['yhat_final'].apply(lambda x: x if x >= 0 else abs(x))

    forecast = forecast.iloc[1:]

    result = [
        ForecastOutput(ds=row['ds'], yhat=row['yhat_final'])
        for _, row in forecast.iterrows()
        if start <= row['ds'] <= end
    ]

    return result

if __name__ == '__main__':
    uvicorn.run(app, host='192.168.0.105', port=1111)