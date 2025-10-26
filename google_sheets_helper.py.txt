import os
import requests
import gspread
from google.oauth2.credentials import Credentials

def get_access_token():
    """Get access token from Replit Connectors API"""
    hostname = os.getenv('REPLIT_CONNECTORS_HOSTNAME')
    
    x_replit_token = None
    if os.getenv('REPL_IDENTITY'):
        x_replit_token = 'repl ' + os.getenv('REPL_IDENTITY')
    elif os.getenv('WEB_REPL_RENEWAL'):
        x_replit_token = 'depl ' + os.getenv('WEB_REPL_RENEWAL')
    
    if not x_replit_token:
        raise Exception('X_REPLIT_TOKEN not found for repl/depl')
    
    response = requests.get(
        f'https://{hostname}/api/v2/connection?include_secrets=true&connector_names=google-sheet',
        headers={
            'Accept': 'application/json',
            'X_REPLIT_TOKEN': x_replit_token
        }
    )
    
    if response.status_code != 200:
        raise Exception(f'Failed to get connection info: {response.status_code} {response.text}')
    
    data = response.json()
    
    if not data.get('items'):
        raise Exception('No Google Sheet connections found. Please set up the Google Sheets connector.')
    
    connection_settings = data['items'][0]
    
    access_token = (
        connection_settings.get('settings', {}).get('access_token') or
        connection_settings.get('settings', {}).get('oauth', {}).get('credentials', {}).get('access_token')
    )
    
    if not access_token:
        raise Exception('Access token not found in connection settings. Please reconnect Google Sheets.')
    
    return access_token

def get_google_sheets_client():
    """Get authenticated gspread client using Replit connector"""
    access_token = get_access_token()
    
    creds = Credentials(token=access_token)
    client = gspread.authorize(creds)
    
    return client
