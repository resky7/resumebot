import os
import requests
import gspread
from google.oauth2.credentials import Credentials
from config import SHEET_NAME


def get_access_token():
    hostname = os.getenv("REPLIT_CONNECTORS_HOSTNAME")

    x_replit_token = None
    if os.getenv("REPL_IDENTITY"):
        x_replit_token = "repl " + os.getenv("REPL_IDENTITY")
    elif os.getenv("WEB_REPL_RENEWAL"):
        x_replit_token = "depl " + os.getenv("WEB_REPL_RENEWAL")

    if not x_replit_token:
        raise Exception("X_REPLIT_TOKEN not found")

    response = requests.get(
        f"https://{hostname}/api/v2/connection?include_secrets=true&connector_names=google-sheet",
        headers={
            "Accept": "application/json",
            "X_REPLIT_TOKEN": x_replit_token
        }
    )

    if response.status_code != 200:
        raise Exception(response.text)

    data = response.json()

    if not data.get("items"):
        raise Exception("Google Sheets connector not configured")

    connection = data["items"][0]

    access_token = (
        connection.get("settings", {}).get("access_token")
        or connection.get("settings", {}).get("oauth", {}).get("credentials", {}).get("access_token")
    )

    if not access_token:
        raise Exception("Access token not found")

    return access_token


def get_google_sheets_client():
    creds = Credentials(token=get_access_token())
    return gspread.authorize(creds)


def save_to_google_sheets(row: list):
    """
    row = ["123456", "Emil", "ru", "2026-01-23"]
    """
    client = get_google_sheets_client()
    sheet = client.open(SHEET_NAME).sheet1

    sheet.append_row(row)
    print("✅ Saved to Google Sheets:", row)

