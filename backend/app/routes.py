import requests
from flask import Blueprint, jsonify, redirect, request, current_app
import logging
from datetime import datetime, timedelta

main = Blueprint('main', __name__)

logging.basicConfig(level=logging.INFO)

@main.route('/api/dexcom/auth', methods=['GET'])
def dexcom_auth():
    logging.info("Received request for /api/dexcom/auth")
    auth_url = f"{current_app.config['DEXCOM_BASE_URL']}/v2/oauth2/login?client_id={current_app.config['DEXCOM_CLIENT_ID']}&redirect_uri={current_app.config['DEXCOM_REDIRECT_URI']}&response_type=code&scope=offline_access"
    logging.info(f"Redirecting to: {auth_url}")
    return redirect(auth_url)

@main.route('/api/dexcom/callback', methods=['GET'])
def dexcom_callback():
    code = request.args.get('code')
    if not code:
        logging.error("No code returned in the callback")
        return jsonify({'error': 'Authorization code not returned'}), 400

    logging.info(f"Received code: {code}")
    token_url = f"{current_app.config['DEXCOM_BASE_URL']}/v2/oauth2/token"
    payload = {
        'client_id': current_app.config['DEXCOM_CLIENT_ID'],
        'client_secret': current_app.config['DEXCOM_CLIENT_SECRET'],
        'code': code,
        'grant_type': 'authorization_code',
        'redirect_uri': current_app.config['DEXCOM_REDIRECT_URI']
    }
    response = requests.post(token_url, data=payload)
    response_data = response.json()
    logging.info(f"Token response: {response_data}")
    access_token = response_data.get('access_token')
    if not access_token:
        logging.error("Access token not returned")
        return jsonify({'error': 'Access token not returned'}), 400

    # Redirect to the frontend with the access token as a URL parameter
    frontend_url = f"http://localhost:3000/?access_token={access_token}"
    return redirect(frontend_url)


@main.route('/api/dexcom/daterange', methods=['GET'])
def dexcom_daterange():
    access_token = request.args.get('access_token')
    if not access_token:
        logging.error("Access token is required")
        return jsonify({'error': 'Access token is required'}), 400

    logging.info(f"Received access token: {access_token}")
    
    # Fetch the date range
    url = f"{current_app.config['DEXCOM_BASE_URL']}/v2/users/self/dataRange"
    headers = {'Authorization': f'Bearer {access_token}'}
    response = requests.get(url, headers=headers)
    logging.info(f"Date range response: {response.text}")

    if response.status_code != 200:
        return jsonify({'error': 'Failed to fetch date range'}), response.status_code

    date_range_data = response.json()
    return jsonify(date_range_data)

@main.route('/api/dexcom/data', methods=['GET'])
def dexcom_data():
    access_token = request.args.get('access_token')
    if not access_token:
        logging.error("Access token is required")
        return jsonify({'error': 'Access token is required'}), 400

    logging.info(f"Received access token: {access_token}")

    # Fetch the date range first
    daterange_url = f"{current_app.config['DEXCOM_BASE_URL']}/v2/users/self/dataRange"
    headers = {'Authorization': f'Bearer {access_token}'}
    response = requests.get(daterange_url, headers=headers)
    logging.info(f"Date range response: {response.text}")

    if response.status_code != 200:
        return jsonify({'error': 'Failed to fetch date range'}), response.status_code

    date_range_data = response.json()

    # Extract startDate and endDate from the date range response for EGVs
    if 'egvs' in date_range_data:
        start_date_str = date_range_data['egvs']['start']['systemTime']
        end_date_str = date_range_data['egvs']['end']['systemTime']
    else:
        logging.error("EGVs data range not found")
        return jsonify({'error': 'EGVs data range not found'}), 400

    logging.info(f"Original startDate: {start_date_str} and endDate: {end_date_str}")

    # Ensure the date range does not exceed 90 days
    start_date = datetime.strptime(start_date_str, '%Y-%m-%dT%H:%M:%S')
    end_date = datetime.strptime(end_date_str, '%Y-%m-%dT%H:%M:%S')
    max_end_date = start_date + timedelta(days=90)

    if end_date > max_end_date:
        end_date = max_end_date
        end_date_str = end_date.strftime('%Y-%m-%dT%H:%M:%S')

    logging.info(f"Adjusted startDate: {start_date_str} and endDate: {end_date_str}")

    # Request glucose data using the adjusted date range
    egvs_url = f"{current_app.config['DEXCOM_BASE_URL']}/v2/users/self/egvs?startDate={start_date_str}&endDate={end_date_str}"
    response = requests.get(egvs_url, headers=headers)
    logging.info(f"EGVS response: {response.text}")

    if response.status_code != 200:
        return jsonify({'error': 'Failed to fetch glucose data'}), response.status_code

    data = response.json()
    logging.info(f"Data response: {data}")
    return jsonify(data)
