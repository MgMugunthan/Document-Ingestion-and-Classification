import os
import base64
import traceback
import time
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from event_emitter import emit_event

SCOPES = ['https://mail.google.com/']

def authenticate_always():
    if os.path.exists('token.json'):
        os.remove('token.json')
    flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
    creds = flow.run_local_server(port=0)
    with open('token.json', 'w') as token:
        token.write(creds.to_json())
    return creds

def fetch_emails_and_ingest_loop():
    creds = authenticate_always()
    service = build('gmail', 'v1', credentials=creds)

    print("[INFO] 🔁 Gmail fetcher started. Polling every 30 seconds...")
    seen_ids = set()

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

                        print(f"[INFO] 📩 From: {sender} -> {filename}")
                        emit_event(
                            file_name=filename,
                            source="email",
                            content_bytes=data,
                            summary=f"Fetched from {sender}",
                            sender=sender
                        )

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