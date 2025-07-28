from email.header import decode_header
from bs4 import BeautifulSoup
import imaplib
import email
from event_emitter import emit_event


def summarize_email(body_text):
    return body_text.strip()[:200] + "..." if body_text else "No summary"

def clean_subject(subject):
    parts = decode_header(subject)
    decoded_parts = []
    for part, encoding in parts:
        if isinstance(part, bytes):
            decoded_parts.append(part.decode(encoding or 'utf-8', errors='ignore'))
        else:
            decoded_parts.append(part)
    return ' '.join(decoded_parts)

def fetch_emails_from_user(user_email, password, imap_server="imap.gmail.com"):
    try:
        mail = imaplib.IMAP4_SSL(imap_server)
        mail.login(user_email, password)
        mail.select("inbox")

        status, messages = mail.search(None, '(UNSEEN)')
        email_ids = messages[0].split()

        if not email_ids:
            return True

        for mail_id in email_ids:
            status, msg_data = mail.fetch(mail_id, "(RFC822)")
            raw_email = msg_data[0][1]
            msg = email.message_from_bytes(raw_email)

            subject = clean_subject(msg["Subject"])
            body_text = ""
            for part in msg.walk():
                content_type = part.get_content_type()
                if content_type == "text/plain":
                    body_text += part.get_payload(decode=True).decode(errors="ignore")
                elif content_type == "text/html":
                    html = part.get_payload(decode=True).decode(errors="ignore")
                    soup = BeautifulSoup(html, "html.parser")
                    body_text += soup.get_text()

            summary = summarize_email(body_text)

            for part in msg.walk():
                content_disposition = part.get("Content-Disposition")
                if content_disposition and "attachment" in content_disposition:
                    filename = part.get_filename()
                    if filename and filename.lower().endswith((".pdf", ".docx", ".txt")):
                        file_data = part.get_payload(decode=True)
                        emit_event(filename, source="email", content_bytes=file_data, summary=summary)

        mail.logout()
        return True
    except Exception as e:
        print(f"[ERROR] {str(e)}")
        return False
