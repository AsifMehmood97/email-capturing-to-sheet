from google.oauth2 import service_account
from googleapiclient.discovery import build
import imaplib
import email
from email.header import decode_header
from datetime import datetime, timezone
import time
from tqdm import tqdm
import requests
from constants import (
    EMAIL,
    PASSWORD,
    IMAP_SERVER,
    INVOICE_API_URL,
    SERVICE_ACCOUNT_FILE,
    SPREADSHEET_ID,
    RANGE_NAME,
    SCOPES,
    CHECK_INTERVAL,
    EXTENSIONS,
)

script_start_time = datetime.now(timezone.utc)

# Authenticate and initialize Sheets API client
credentials = service_account.Credentials.from_service_account_file(
    SERVICE_ACCOUNT_FILE,
    scopes=SCOPES
)
service = build('sheets', 'v4', credentials=credentials)

def add_row_to_sheet(row_dict, filename):
    row_values = [
        filename,
        row_dict["Invoice No"],
        row_dict["Gross / Brutto"],
        row_dict["Net / Netto"],
        row_dict["VAT"]["total_value"],
        row_dict["Currency"],
        row_dict["Issue date"],
        row_dict["Type"],
        row_dict["Provider VAT ID"],
        row_dict["Provider name"],
        row_dict["Provider address"],
        row_dict["Provider country"],
        row_dict["Code 1"],
        row_dict["Subcode"]
    ]

    # Prepare the data to append as a new row
    body = {'values': [row_values]}

    # Make the request to append the data
    request = service.spreadsheets().values().append(
        spreadsheetId=SPREADSHEET_ID,
        range=RANGE_NAME,
        valueInputOption='USER_ENTERED',  # Use USER_ENTERED to auto-format the values
        insertDataOption='INSERT_ROWS',
        body=body
    )

    try:
        response = request.execute()
        print(response)
    except Exception as e:
        print(f"Error: {e}")

def request_invoice_api(file_content, filename):
    files = {"files": (filename, file_content)}
    response = requests.post(INVOICE_API_URL, files=files)
    if response.status_code == 200:
        return response.json()
    return ""

def process_email(msg):
    subject, encoding = decode_header(msg["Subject"])[0]
    if isinstance(subject, bytes):
        subject = subject.decode(encoding if encoding else 'utf-8')
    from_ = msg.get("From")
    if msg.is_multipart():
        for part in msg.walk():
            content_type = part.get_content_type()
            content_disposition = str(part.get("Content-Disposition"))
            if "attachment" in content_disposition:
                filename = part.get_filename()
                if filename:
                    filename, encoding = decode_header(filename)[0]
                    if isinstance(filename, bytes):
                        filename = filename.decode(encoding if encoding else 'utf-8')
                    if filename.lower().endswith(EXTENSIONS):
                        file_content = part.get_payload(decode=True)
                        response = request_invoice_api(file_content, filename)
                        if response:
                            file_name_key = list(response.keys())[0]
                            add_row_to_sheet(response[file_name_key],file_name_key)
                        else:
                            print(f"Failed to process {filename}.")

def check_inbox():
    try:
        mail = imaplib.IMAP4_SSL(IMAP_SERVER)
        mail.login(EMAIL, PASSWORD)
        mail.select("inbox")
        status, messages = mail.search(None, 'UNSEEN')
        email_ids = messages[0].split()
        print(email_ids)
        if not email_ids:
            print("No new emails.")
            return
        for email_id in tqdm(email_ids):
            status, msg_data = mail.fetch(email_id, "(RFC822)")
            for response_part in msg_data:
                if isinstance(response_part, tuple):
                    msg = email.message_from_bytes(response_part[1])
                    email_date = msg.get("Date")
                    email_datetime = email.utils.parsedate_to_datetime(email_date)
                    if email_datetime > script_start_time:
                        process_email(msg)
        for email_id in email_ids:
            mail.store(email_id, '+FLAGS', '\\Seen')
        mail.logout()
    except Exception as e:
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    while True:
        check_inbox()
        print(f"Waiting for {CHECK_INTERVAL} secs to check again...")
        time.sleep(CHECK_INTERVAL)
