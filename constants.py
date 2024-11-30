import os

EMAIL = os.environ.get("EMAIL")
PASSWORD = os.environ.get("PASSWORD")
IMAP_SERVER = os.environ.get("IMAP_SERVER")
INVOICE_API_URL = os.environ.get("INVOICE_API_URL")
SERVICE_ACCOUNT_FILE = os.environ.get("SERVICE_ACCOUNT_FILE")
SPREADSHEET_ID = os.environ.get("SPREADSHEET_ID")
RANGE_NAME = os.environ.get("RANGE_NAME")
SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
CHECK_INTERVAL = int(os.environ.get("CHECK_INTERVAL")) or 10
EXTENSIONS = (
    extension for extension in os.environ.get("EXTENSIONS").split(',')
) or ('.png', '.jpeg', '.jpg', '.pdf')