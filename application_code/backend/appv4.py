import os
from flask import Flask, jsonify, request
from flask_cors import CORS
import numpy as np
import pandas as pd
from datetime import timedelta
from joblib import load


app = Flask(__name__)
CORS(app)

# Load the model
model = load('models/Electricity_Price_model.pkl')

# Load the data
def load_data():
    file_path = 'data/Data_Combined_2023-2024_daily.csv'
    data = pd.read_csv(file_path)

    # Drop the unnecessary index column
    data.drop(columns=['Unnamed: 0'], inplace=True)

    # Convert date column to datetime format and set as index
    data['Date'] = pd.to_datetime(data['Date'])
    data.set_index('Date', inplace=True)

    # Drop the Gas Demand column
    data.drop(columns=['Gas Demand'], inplace=True)

    # Handle missing values
    data['Gas Price'].fillna(method='ffill', inplace=True)
    data['interconn_fra'].fillna(method='ffill', inplace=True)

    # Forward fill first, then backward fill
    data['CO2_Value'].fillna(method='ffill', inplace=True)
    data['CO2_Value'].fillna(method='bfill', inplace=True)

    # Rename columns
    data.rename(columns={'Electricity Demand': 'Electricity_Demand', 'Gas Price': 'Gas_Price', 'Electricity Price': 'Electricity_Price'}, inplace=True)

    # Compute lags and moving averages
    data['lag_1'] = data['Electricity_Price'].shift(1)
    data['lag_7'] = data['Electricity_Price'].shift(7)
    data['ma_7'] = data['Electricity_Price'].rolling(window=7).mean()
    data['ma_30'] = data['Electricity_Price'].rolling(window=30).mean()
    
    print(data.tail())

    data.dropna(inplace=True)

    latest_date = data.index.max()
    
    return data, latest_date

# Function to read and process the CSV file
def get_data():
    df, _ = load_data()
    print(df.columns)
    print(df.head())
    # Find the most recent date in the DataFrame
    df = df.reset_index()
    max_date = df['Date'].max()
    # Calculate the start date for the last year period
    start_date = max_date - timedelta(days=365)
    
    # Filter the DataFrame for the last year
    last_year_df = df[df["Date"] >= start_date]
    
    # Convert to dictionary: Date as key, Electricity Price as value
    last_year_data = {row["Date"].strftime('%Y-%m-%d'): row['Electricity_Price'] for _, row in last_year_df.iterrows()}
    
    return {'hist': last_year_data}

def predict_future_values(var_names, end_date, data):
    for var_name in var_names:
        # Load the model for the specified variable
        model = load(f"models/{var_name}_model.pkl")
        var_lags = pd.read_csv(f'data/{var_name}_lags.csv', index_col='Date', parse_dates=True)
        
        # Convert end_date to pandas Timestamp
        end_date = pd.to_datetime(end_date)
        
        # Make sure the index is in datetime format and the DataFrame is sorted by index
        var_lags.index = pd.to_datetime(var_lags.index)
        var_lags = var_lags.sort_index()
        
        # Start predicting from the day after the latest date in var_lags
        current_date = var_lags.index.max() + timedelta(days=1)
        
        while current_date <= end_date:
            print(f'Predicting {var_name} for {current_date}')
            # Extract the last 15 entries to calculate lags
            last_entries = var_lags.tail(15)
            new_row = {f'{var_name}_lag{i}': last_entries[var_name].shift(i-1).iloc[-1] for i in range(1, 16)}
            
            # Prepare features and predict
            features = [new_row[f'{var_name}_lag{i}'] for i in range(1, 16)]
            predicted_value = model.predict([features])[0]
            
            # Append new row to DataFrame with current_date as the index
            new_row[var_name] = predicted_value
            var_lags.loc[current_date] = new_row
            
            # Add the prediction to the data DataFrame
            if var_name not in data.columns:
                data[var_name] = pd.NA
            data.loc[current_date, var_name] = predicted_value
            
            # Increment the date by one day
            current_date += timedelta(days=1)      

    print(data.tail(50))

    return data

def prep_for_model(data_predict):
    # Prepare the data (assuming data is already loaded in a DataFrame called 'data')
    data_predict = data_predict.reset_index().rename(columns={'Date': 'ds', 'Electricity_Price': 'y'})

    # Create lagged features, moving averages, and interaction terms
    data_predict['lag_1'] = data_predict['y'].shift(1)
    data_predict['lag_7'] = data_predict['y'].shift(7)
    data_predict['ma_7'] = data_predict['y'].rolling(window=7).mean()
    data_predict['ma_30'] = data_predict['y'].rolling(window=30).mean()

    data_predict['interaction_1'] = data_predict['Gas_Price'] * data_predict['CO2_Value']
    data_predict['interaction_2'] = data_predict['Temperature'] * data_predict['Electricity_Demand']
    data_predict['interaction_3'] = data_predict['Gas_Price'] * data_predict['Electricity_Demand']
    data_predict['interaction_4'] = data_predict['Temperature'] * data_predict['Gas_Price']

    return data_predict

def recursive_forecast(historical_data, forecast_dates):
    # Initialize predictions list
    predictions = []

    for current_date in forecast_dates:
        current_date = current_date.strftime('%Y-%m-%d')

        # Create lagged features, moving averages
        historical_data['lag_1'] = historical_data['y'].shift(1)
        historical_data['lag_7'] = historical_data['y'].shift(7)
        historical_data['ma_7'] = historical_data['y'].shift(1).rolling(window=7).mean()
        historical_data['ma_30'] = historical_data['y'].shift(1).rolling(window=30).mean()

        print(historical_data[['lag_1', 'lag_7', 'ma_7', 'ma_30']].tail(50))

        row_exog = historical_data[historical_data['ds'] == current_date].drop(columns=['y', 'ds']).values.tolist()

        print(row_exog)

        # Make the forecast for the current date
        forecast = model.get_forecast(steps=1, exog=row_exog)
        forecast_mean = forecast.predicted_mean
        forecast_ci = forecast.conf_int()

        # Append the forecast to predictions
        predictions.append((current_date, forecast_mean.values[0], forecast_ci.iloc[0, 0], forecast_ci.iloc[0, 1]))

        # Update historical data with the new forecasted value
        historical_data.loc[historical_data['ds'] == current_date, 'y'] = forecast_mean.values[0]

    # Prepare data to be returned
    historical_data = historical_data.loc[historical_data['ds'] < forecast_dates[0]]
    predicted_data = pd.DataFrame(predictions, columns=['ds', 'y', 'yhat_lower', 'yhat_upper'])

    return historical_data, predicted_data

@app.route('/get-graph', methods=['GET'])
def get_graph():
    data = get_data()
    return jsonify(data)

@app.route('/predict', methods=['POST'])
def predict():
    # Get the request data
    form = request.form
    end_date = form['end_date']
    data, latest_date = load_data()
    start_date = latest_date + timedelta(days=1)

    var_names = ['Temperature', 'Gas_Price', 'interconn_fra', 'CO2_Value', 'Electricity_Demand']
    data_predict = predict_future_values(var_names, end_date, data)
    data_predict = prep_for_model(data_predict)
    forecast_dates = pd.date_range(start=start_date, end=end_date)

    # Make recursive forecast
    _, pred = recursive_forecast(data_predict, forecast_dates)

    # Convert to dictionary: Date as key, Electricity Price as value
    hist_data = get_data()
    predicted_values = {row["ds"]: {'pred': row['y'], 'pred_lower': row['yhat_lower'], 'pred_upper': row['yhat_upper']} for _, row in pred.iterrows()}

    # Prepare the predictions for sending
    return jsonify(hist_data, 
                   {'pred': predicted_values})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)