import os
import base64
import traceback
import time
from datetime import datetime
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from event_emitter import emit_event
from config import FILES_DIR

# Scope for read & modify access
SCOPES = ['https://www.googleapis.com/auth/gmail.modify']


def authenticate_always():
    """Force Google login each time"""
    if os.path.exists('token.json'):
        os.remove('token.json')
    flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
    creds = flow.run_local_server(port=8080)
    with open('token.json', 'w') as token:
        token.write(creds.to_json())
    return creds


def fetch_emails_and_ingest_loop():
    creds = authenticate_always()
    service = build('gmail', 'v1', credentials=creds)

    login_timestamp = int(time.time() * 1000)  # Gmail internalDate is in ms
    seen_ids = set()

    print("[INFO] ✅ Gmail connected.")
    print("[INFO] 🔁 Gmail fetcher started. Polling every 30 seconds...")

    while True:
        try:
            response = service.users().messages().list(
                userId='me',
                q='has:attachment is:unread',
                labelIds=['INBOX']
            ).execute()

            messages = response.get('messages', [])

            for msg in messages:
                msg_id = msg['id']
                if msg_id in seen_ids:
                    continue

                msg_data = service.users().messages().get(userId='me', id=msg_id).execute()

                # Get time the email was received
                email_timestamp = int(msg_data.get('internalDate', 0))
                if email_timestamp < login_timestamp:
                    continue  # Skip old emails

                headers = msg_data.get('payload', {}).get('headers', [])
                sender = next((h['value'] for h in headers if h['name'] == 'From'), 'Unknown')
                parts = msg_data.get('payload', {}).get('parts', [])

                for part in parts:
                    filename = part.get("filename")
                    body = part.get("body", {})
                    if filename and 'attachmentId' in body:
                        attachment = service.users().messages().attachments().get(
                            userId='me',
                            messageId=msg_id,
                            id=body['attachmentId']
                        ).execute()

                        data = base64.urlsafe_b64decode(attachment['data'].encode('UTF-8'))

                        print(f"[INFO] 📩 New Mail from: {sender} -> {filename}")
                        emit_event(
                            file_name=filename,
                            source="email",
                            content_bytes=data,
                            summary=f"Fetched from {sender}",
                            sender=sender
                        )

                # Mark email as read
                service.users().messages().modify(
                    userId='me',
                    id=msg_id,
                    body={'removeLabelIds': ['UNREAD']}
                ).execute()

                seen_ids.add(msg_id)

        except Exception as e:
            print(f"[ERROR] Fetching failed: {e}")
            traceback.print_exc()

        time.sleep(30)
