from flask import Flask, render_template, send_file
import pandas as pd
import json

app = Flask(__name__)

# Load the data once
DATA_PATH = 'bitcoin_full_data.csv'
data = pd.read_csv(DATA_PATH)
data['Date'] = pd.to_datetime(data['Date'])
data = data.sort_values('Date')

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/dashboard')
def dashboard():
    sample = data.tail(50)  # Use only the last 50 rows for clarity
    labels = sample['Date'].dt.strftime('%Y-%m-%d %H:%M').tolist()
    price_data = sample['Price'].tolist()
    volume_data = sample['total_volume'].tolist()
    market_cap_data = sample['market_cap'].tolist()
    price_change_24h = sample['price_change_24h'].fillna(0).tolist()

    return render_template(
        'dashboard.html',
        labels=json.dumps(labels),
        price_data=json.dumps(price_data),
        volume_data=json.dumps(volume_data),
        market_cap_data=json.dumps(market_cap_data),
        price_change_24h=json.dumps(price_change_24h),
        explain_price="This chart shows how Bitcoin's price changes over time, helping identify peaks and valleys.",
        explain_volume="This bar chart compares total volume and market cap, offering insight into trading activity.",
        explain_change="This chart displays short-term price fluctuations over the past 24 hours."
    )

@app.route('/forecast')
def forecast():
    from sklearn.ensemble import RandomForestRegressor
    from sklearn.metrics import r2_score, mean_absolute_error
    import numpy as np

    df = data.copy()
    df['Timestamp'] = df['Date'].astype(int) / 10**9
    X = df[['Timestamp']]
    y = df['Price']

    model = RandomForestRegressor(n_estimators=100, random_state=42)
    model.fit(X, y)
    y_pred = model.predict(X)

    labels = df['Date'].dt.strftime('%Y-%m-%d').tolist()
    actual_prices = y.tolist()
    predicted_prices = y_pred.tolist()

    r2 = round(r2_score(y, y_pred), 4)
    mae = round(mean_absolute_error(y, y_pred), 2)

    return render_template(
        'forecast.html',
        labels=json.dumps(labels),
        actual_prices=json.dumps(actual_prices),
        predicted_prices=json.dumps(predicted_prices),
        r2_score=r2,
        mae=mae,
        model_explanation="We used a Random Forest Regressor, which captures complex patterns and improves prediction accuracy over simple linear models.",
        improvement_note="Further improvements can be achieved by hyperparameter tuning or using gradient-based models like XGBoost."
    )

@app.route('/download')
def download():
    return send_file(DATA_PATH, as_attachment=True)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
