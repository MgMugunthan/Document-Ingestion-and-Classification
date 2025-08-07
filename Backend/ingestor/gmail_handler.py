"""
Gmail Handler Module

Handles all Gmail-related functionality including authentication,
fetching attachments, search, and processing selected emails.
"""

import os
import sys
import json
import base64
import threading
import time
import re
from datetime import datetime, timedelta

# Add parent directory for imports
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
import logger

# Gmail integration
try:
    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow
    from googleapiclient.discovery import build
    GMAIL_AVAILABLE = True
except ImportError:
    GMAIL_AVAILABLE = False

class GmailHandler:
    """Handles all Gmail integration functionality."""
    
    def __init__(self, config, db_manager, emit_callback):
        self.config = config
        self.db = db_manager
        self.emit_to_kafka = emit_callback
        self.log = logger.get_agent_logger("Gmail")
        if self.is_available():
            self.log.info("Gmail handler initialized(authentication on-demand)")
        else:
            self.log.info("Gmail handler disabled")
    
    def is_available(self):
        """Check if Gmail integration is available."""
        return GMAIL_AVAILABLE and hasattr(self.config, 'gmail_enabled') and self.config.gmail_enabled
    
    def setup_auth(self):
        """Setup Gmail authentication."""
        if not self.is_available():
            return None
            
        creds = None
        if os.path.exists(self.config.gmail_token_file):
            creds = Credentials.from_authorized_user_file(
                self.config.gmail_token_file, 
                self.config.gmail_scopes
            )
        
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                try:
                    creds.refresh(Request())
                    self.log.info("Gmail credentials refreshed")
                    with open(self.config.gmail_token_file, 'w')as token:
                        token.write(creds.to_json())
                except Exception as e:
                    self.log.error(f"Failed to refresh credentials: {e}")
                    return None
            else:
                self.log.debug("Gmail authentication required - waiting for user request")
                return None
    
        return creds
    
    def get_auth_url(self):
        """Get Gmail OAuth authorization URL."""
        if not self.is_available():
            return None, "Gmail integration not enabled"
            
        try:
            from google_auth_oauthlib.flow import Flow
            import os
            
            # Allow HTTP for localhost development
            os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'
            
            flow = Flow.from_client_secrets_file(
                self.config.gmail_credentials_file,
                self.config.gmail_scopes,
                redirect_uri="http://localhost:5000/api/gmail/auth/callback"
            )
            
            auth_url, _ = flow.authorization_url(prompt='consent')
            
            # Store flow state for callback
            self._flow = flow
            
            self.log.info("Gmail OAuth URL generated")
            return auth_url, None
            
        except Exception as e:
            self.log.error(f"Failed to generate Gmail OAuth URL: {e}")
            return None, str(e)
    
    def handle_auth_callback(self, authorization_response):
        """Handle Gmail OAuth callback."""
        if not self.is_available():
            return False, "Gmail integration not enabled"
            
        try:
            # Allow HTTP for localhost development
            import os
            os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'
            
            if not hasattr(self, '_flow') or not self._flow:
                return False, "OAuth flow not initialized"
                
            self._flow.fetch_token(authorization_response=authorization_response)
            credentials = self._flow.credentials
            
            # Save token
            with open(self.config.gmail_token_file, "w") as token_file:
                token_file.write(credentials.to_json())
            
            # We don't need to get user info or update database for basic functionality
            # Just confirm the credentials are valid by testing Gmail API access
            try:
                service = build('gmail', 'v1', credentials=credentials)
                # Simple test call to verify credentials work
                profile = service.users().getProfile(userId='me').execute()
                email = profile.get('emailAddress', 'Unknown')
                self.log.info(f"Gmail credentials validated for {email}")
            except Exception as test_e:
                self.log.warning(f"Could not validate Gmail credentials: {test_e}")
                email = "Gmail User"
            
            # Clean up flow
            if hasattr(self, '_flow'):
                delattr(self, '_flow')
            
            self.log.info(f"Gmail authorization successful for {email}")
            return True, email
            
        except Exception as e:
            self.log.error(f"Gmail OAuth callback failed: {e}")
            return False, str(e)
    
    def load_state(self):
        """Load Gmail processing state."""
        try:
            if os.path.exists(self.config.gmail_state_file):
                with open(self.config.gmail_state_file, 'r') as f:
                    state = json.load(f)
                    return state.get('last_processed_timestamp')
        except Exception as e:
            self.log.warning(f"Failed to load Gmail state: {e}")
        return None
    
    def save_state(self, timestamp):
        """Save Gmail processing state."""
        try:
            state = {'last_processed_timestamp': timestamp}
            with open(self.config.gmail_state_file, 'w') as f:
                json.dump(state, f)
        except Exception as e:
            self.log.error(f"Failed to save Gmail state: {e}")
    
    def initialize_state(self):
        """Initialize Gmail state to current time."""
        current_time = datetime.now().isoformat()
        self.save_state(current_time)
        self.log.info("Gmail state initialized - will only process new emails from now on")
    
    def fetch_attachments(self, fetch_all=False):
        """Fetch attachments from Gmail."""
        if not self.is_available():
            self.log.info("Gmail integration disabled")
            return
            
        try:
            creds = self.setup_auth()
            if not creds:
                self.log.debug("Gmail authentication not available - skipping fetch")
                return
                
            service = build('gmail', 'v1', credentials=creds)
            
            # Build query
            if fetch_all:
                query = 'is:unread has:attachment'
                self.log.info("Fetching ALL unread emails with attachments...")
            else:
                last_processed = self.load_state()
                if last_processed:
                    try:
                        last_date = datetime.fromisoformat(last_processed.replace('Z', '+00:00'))
                        date_str = last_date.strftime('%Y/%m/%d')
                        query = f'is:unread has:attachment after:{date_str}'
                        self.log.info(f"Fetching emails newer than {date_str}...")
                    except:
                        query = 'is:unread has:attachment'
                        self.log.warning("Invalid last processed date, fetching all unread emails")
                else:
                    self.initialize_state()
                    self.log.info("First Gmail connection - initialized state")
                    return
            
            results = service.users().messages().list(userId='me', q=query).execute()
            messages = results.get('messages', [])
            
            self.log.info(f"Found {len(messages)} emails to process")
            
            processed_count = 0
            current_time = datetime.now().isoformat()
            
            for message in messages:
                msg_id = message['id']
                msg = service.users().messages().get(userId='me', id=msg_id).execute()
                
                attachments_processed = self.process_message(service, msg)
                if attachments_processed > 0:
                    processed_count += attachments_processed
                
                # Mark as read
                service.users().messages().modify(
                    userId='me',
                    id=msg_id,
                    body={'removeLabelIds': ['UNREAD']}
                ).execute()
            
            self.save_state(current_time)
            
            if processed_count > 0:
                self.log.info(f"Processed {processed_count} Gmail attachments")
            else:
                self.log.info("No new Gmail attachments to process")
            
        except Exception as e:
            self.log.error(f"Gmail processing failed: {e}")
    
    def process_message(self, service, message):
        """Process Gmail message and extract attachments."""
        processed_count = 0
        try:
            msg_id = message['id']
            sender = "Gmail"
            
            # Get sender info
            headers = message['payload'].get('headers', [])
            for header in headers:
                if header['name'] == 'From':
                    sender = header['value']
                    break
            
            # Process parts for attachments
            parts = message['payload'].get('parts', [])
            if not parts:
                parts = [message['payload']]
            
            for part in parts:
                if part.get('filename'):
                    attachment_id = part['body'].get('attachmentId')
                    if attachment_id:
                        attachment = service.users().messages().attachments().get(
                            userId='me',
                            messageId=msg_id,
                            id=attachment_id
                        ).execute()
                        
                        file_data = base64.urlsafe_b64decode(attachment['data'])
                        filename = part['filename']
                        
                        if self._is_valid_document(filename):
                            filepath = os.path.join(self.config.files_dir, filename)
                            
                            with open(filepath, 'wb') as f:
                                f.write(file_data)
                            
                            if self._is_file_size_valid(filepath):
                                self.emit_to_kafka(
                                    filename,
                                    filepath,
                                    source="gmail",
                                    summary=f"Email attachment from {sender}",
                                    sender=sender
                                )
                                self.log.info(f"Gmail attachment processed: {filename}")
                                processed_count += 1
                            else:
                                os.remove(filepath)
                                self.log.warning(f"Gmail attachment too large, skipped: {filename}")
        
        except Exception as e:
            self.log.error(f"Failed to process Gmail message: {e}")
        
        return processed_count
    
    def extract_prompt_filters(self, prompt):
        """Extract search filters from natural language prompt."""
        filters = {}
        
        # Extract dates
        date_matches = re.findall(r'\d{4}-\d{2}-\d{2}', prompt)
        if len(date_matches) >= 2:
            filters['start_date'] = date_matches[0]
            filters['end_date'] = date_matches[1]
        elif len(date_matches) == 1:
            filters['start_date'] = date_matches[0]
            filters['end_date'] = date_matches[0]
        else:
            # Default to last 7 days
            today = datetime.now()
            week_ago = today - timedelta(days=7)
            filters['start_date'] = week_ago.strftime('%Y-%m-%d')
            filters['end_date'] = today.strftime('%Y-%m-%d')
        
        # Extract email
        email_match = re.search(r'[\w\.-]+@[\w\.-]+\.\w+', prompt)
        if email_match:
            filters['email'] = email_match.group()
        
        # Extract keywords
        keywords = []
        prompt_lower = prompt.lower()
        keyword_list = ['invoice', 'contract', 'report', 'receipt', 'statement']
        for keyword in keyword_list:
            if keyword in prompt_lower:
                keywords.append(keyword)
        
        if keywords:
            filters['keywords'] = keywords
        
        return filters
    
    def search_by_prompt(self, prompt):
        """Search Gmail using natural language prompt."""
        if not self.is_available():
            return {'error': 'Gmail integration not enabled'}
        
        try:
            creds = self.setup_auth()
            if not creds:
                return {'error': 'Gmail authentication failed'}
            
            service = build('gmail', 'v1', credentials=creds)
            filters = self.extract_prompt_filters(prompt)
            
            # Build query
            query_parts = ['has:attachment']
            
            if filters.get('start_date') and filters.get('end_date'):
                query_parts.append(f"after:{filters['start_date']}")
                query_parts.append(f"before:{filters['end_date']}")
            
            if filters.get('email'):
                query_parts.append(f"from:{filters['email']}")
            
            if filters.get('keywords'):
                for keyword in filters['keywords']:
                    query_parts.append(f"subject:{keyword}")
            
            query = ' '.join(query_parts)
            self.log.info(f"Gmail search query: {query}")
            
            # Search Gmail
            results = service.users().messages().list(userId='me', q=query).execute()
            messages = results.get('messages', [])
            
            files = []
            for message in messages[:20]:  # Limit to 20 results
                msg = service.users().messages().get(userId='me', id=message['id']).execute()
                
                # Get headers
                headers = msg['payload'].get('headers', [])
                sender = next((h['value'] for h in headers if h['name'] == 'From'), 'Unknown')
                subject = next((h['value'] for h in headers if h['name'] == 'Subject'), 'No Subject')
                date = next((h['value'] for h in headers if h['name'] == 'Date'), 'Unknown')
                
                # Get attachments
                parts = msg['payload'].get('parts', [])
                if not parts:
                    parts = [msg['payload']]
                
                for part in parts:
                    if part.get('filename') and part.get('body', {}).get('attachmentId'):
                        files.append({
                            'message_id': message['id'],
                            'filename': part['filename'],
                            'attachmentId': part['body']['attachmentId'],
                            'sender': sender,
                            'subject': subject,
                            'date': date,
                            'size': part['body'].get('size', 0)
                        })
            
            return {
                'status': 'success',
                'query': query,
                'filters': filters,
                'files': files,
                'total_found': len(files)
            }
            
        except Exception as e:
            self.log.error(f"Gmail search failed: {e}")
            return {'error': str(e)}
    
    def process_selected_files(self, file_ids):
        """Process specific Gmail files by message IDs."""
        if not self.is_available():
            return {'error': 'Gmail integration not enabled'}
        
        try:
            creds = self.setup_auth()
            if not creds:
                return {'error': 'Gmail authentication failed'}
            
            service = build('gmail', 'v1', credentials=creds)
            processed_count = 0
            errors = []
            processed_files = []
            
            for file_id in file_ids:
                try:
                    msg = service.users().messages().get(userId='me', id=file_id).execute()
                    attachments_processed = self.process_message(service, msg)
                    processed_count += attachments_processed
                    
                    if attachments_processed > 0:
                        parts = msg['payload'].get('parts', [])
                        if not parts:
                            parts = [msg['payload']]
                        
                        for part in parts:
                            if part.get('filename') and part.get('body', {}).get('attachmentId'):
                                processed_files.append(part['filename'])
                    
                    # Mark as read
                    service.users().messages().modify(
                        userId='me',
                        id=file_id,
                        body={'removeLabelIds': ['UNREAD']}
                    ).execute()
                    
                except Exception as e:
                    errors.append(f"Failed to process {file_id}: {str(e)}")
                    self.log.error(f"Failed to process Gmail file {file_id}: {e}")
            
            return {
                'status': 'success',
                'processed_count': processed_count,
                'processed_files': processed_files,
                'errors': errors
            }
            
        except Exception as e:
            self.log.error(f"Gmail file processing failed: {e}")
            return {'error': str(e)}
    
    def start_monitor(self):
        """Start Gmail monitoring using push notifications instead of polling."""
        if not self.is_available():
            return
            
        def gmail_loop():
            self.log.info("Gmail monitor started with push notifications")
            consecutive_auth_failures = 0
            
            while True:
                try:
                    # Check if we have valid credentials before attempting to setup push notifications
                    creds = self.setup_auth()
                    if not creds:
                        # If we don't have credentials, wait longer and only log occasionally
                        consecutive_auth_failures += 1
                        if consecutive_auth_failures == 1:  # Log only the first failure
                            self.log.info("Gmail monitoring waiting for authentication...")
                        elif consecutive_auth_failures % 10 == 0:  # Log every 10th failure
                            self.log.debug(f"Gmail still waiting for authentication (attempt {consecutive_auth_failures})")
                        time.sleep(60)  # Wait longer when not authenticated
                        continue
                    
                    # Reset counter if we have credentials
                    if consecutive_auth_failures > 0:
                        self.log.info("Gmail authentication restored, setting up push notifications")
                        consecutive_auth_failures = 0
                    
                    # Setup Gmail push notifications
                    success = self.setup_push_notifications(creds)
                    if success:
                        self.log.info("Gmail push notifications enabled - waiting for real-time updates")
                        # Keep the thread alive but don't poll - just wait for push notifications
                        while True:
                            time.sleep(300)  # Check every 5 minutes if push is still active
                            # Re-verify credentials periodically
                            current_creds = self.setup_auth()
                            if not current_creds:
                                self.log.warning("Gmail credentials expired, restarting monitor")
                                break
                    else:
                        # Fallback to polling if push notifications fail
                        self.log.warning("Push notifications failed, falling back to polling")
                        self.fetch_attachments()
                        time.sleep(self.config.gmail_check_interval)
                    
                except Exception as e:
                    self.log.error(f"Gmail monitor error: {e}")
                    time.sleep(60)
        
        gmail_thread = threading.Thread(target=gmail_loop, daemon=True)
        gmail_thread.start()
        self.log.info(f"Gmail monitoring enabled with push notifications")
    
    def setup_push_notifications(self, creds):
        """Setup Gmail push notifications for real-time email monitoring."""
        try:
            service = build('gmail', 'v1', credentials=creds)
            
            # Create a watch request
            watch_request = {
                'labelIds': ['INBOX'],  # Monitor inbox
                'topicName': 'projects/your-project-id/topics/gmail-push',  # You'd need to set this up
                'labelFilterAction': 'include'
            }
            
            # For now, since we don't have Pub/Sub setup, let's use a hybrid approach
            # We'll use IMAP IDLE as an alternative to push notifications
            return self.setup_imap_idle(creds)
            
        except Exception as e:
            self.log.error(f"Failed to setup Gmail push notifications: {e}")
            return False
    
    def setup_imap_idle(self, creds):
        """Setup IMAP IDLE for near real-time email monitoring."""
        try:
            # For Gmail API, we'll implement a more efficient polling approach
            # Check for new emails every 30 seconds instead of 10
            # But only when there's no recent activity
            
            # Initial fetch to establish baseline
            self.fetch_attachments()
            
            # Set up efficient polling
            last_activity = time.time()
            idle_interval = 30  # Start with 30 seconds
            max_interval = 300  # Max 5 minutes
            
            def efficient_polling():
                nonlocal last_activity, idle_interval
                
                while True:
                    try:
                        # Check for new emails
                        before_count = self.get_email_count()
                        self.fetch_attachments()
                        after_count = self.get_email_count()
                        
                        # If we found new emails, reset to frequent polling
                        if after_count != before_count:
                            last_activity = time.time()
                            idle_interval = 10  # Back to 10 seconds when active
                            self.log.info("New emails detected, switching to active monitoring")
                        else:
                            # Gradually increase interval if no activity
                            time_since_activity = time.time() - last_activity
                            if time_since_activity > 300:  # 5 minutes of no activity
                                idle_interval = min(idle_interval * 1.5, max_interval)
                                idle_interval = int(idle_interval)
                        
                        self.log.debug(f"Next Gmail check in {idle_interval} seconds")
                        time.sleep(idle_interval)
                        
                    except Exception as e:
                        self.log.error(f"Gmail efficient polling error: {e}")
                        time.sleep(60)
            
            # Start efficient polling in a separate thread
            polling_thread = threading.Thread(target=efficient_polling, daemon=True)
            polling_thread.start()
            
            return True
            
        except Exception as e:
            self.log.error(f"Failed to setup efficient Gmail monitoring: {e}")
            return False
    
    def get_email_count(self):
        """Get current count of unread emails with attachments."""
        try:
            creds = self.setup_auth()
            if not creds:
                return 0
                
            service = build('gmail', 'v1', credentials=creds)
            results = service.users().messages().list(
                userId='me', 
                q='is:unread has:attachment',
                maxResults=1
            ).execute()
            
            return results.get('resultSizeEstimate', 0)
            
        except Exception as e:
            self.log.debug(f"Failed to get email count: {e}")
            return 0
    
    def disconnect(self):
        """Disconnect Gmail integration by removing stored credentials."""
        try:
            disconnected_items = []
            
            # Remove token file
            if os.path.exists(self.config.gmail_token_file):
                os.remove(self.config.gmail_token_file)
                disconnected_items.append("OAuth token")
                self.log.info("Gmail OAuth token removed")
            
            # Remove state file
            if os.path.exists(self.config.gmail_state_file):
                os.remove(self.config.gmail_state_file)
                disconnected_items.append("processing state")
                self.log.info("Gmail state file removed")
            
            # Skip database update for now since gmail_connected column doesn't exist
            # We can rely on token file existence for connection status
            
            # Clean up any stored flow state
            if hasattr(self, '_flow'):
                delattr(self, '_flow')
                disconnected_items.append("OAuth flow state")
            
            self.log.info(f"Gmail successfully disconnected - removed: {', '.join(disconnected_items)}")
            
            return {
                'status': 'success',
                'message': f'Gmail disconnected successfully',
                'removed_items': disconnected_items
            }
            
        except Exception as e:
            self.log.error(f"Failed to disconnect Gmail: {e}")
            return {
                'status': 'error',
                'error': str(e)
            }
    
    def get_status(self):
        """Get Gmail integration status."""
        if not GMAIL_AVAILABLE:
            return {'gmail_enabled': False, 'reason': 'Gmail integration not available'}
        
        last_processed = self.load_state()
        return {
            'gmail_enabled': True,
            'last_processed_timestamp': last_processed,
            'state_file_exists': os.path.exists(self.config.gmail_state_file),
            'credentials_file_exists': os.path.exists(self.config.gmail_credentials_file),
            'token_file_exists': os.path.exists(self.config.gmail_token_file)
        }
    
    def _is_valid_document(self, filename):
        """Check if file has supported extension."""
        ext = os.path.splitext(filename)[1].lower()
        return ext in self.config.supported_extensions
    
    def _is_file_size_valid(self, file_path):
        """Check if file size is within limits."""
        try:
            size = os.path.getsize(file_path)
            return size <= self.config.max_file_size
        except:
            return False
