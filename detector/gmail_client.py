import os
import pickle
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import base64
import re
from concurrent.futures import ThreadPoolExecutor, as_completed

# Scopes required for reading Gmail
SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']

class GmailClient:
    def __init__(self, credentials_file='credentials.json', token_file='token.pickle'):
        self.credentials_file = credentials_file
        self.token_file = token_file
        self.service = None
        
    def authenticate(self, user_id=None):
        """Authenticate user and return Gmail service."""
        creds = None
        
        # Use user-specific token file if user_id provided
        if user_id:
            self.token_file = f'token_{user_id}.pickle'
        
        # Token file stores the user's access and refresh tokens
        if os.path.exists(self.token_file):
            with open(self.token_file, 'rb') as token:
                creds = pickle.load(token)
        
        # If there are no valid credentials, let user log in
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    self.credentials_file, SCOPES)
                # Use run_local_server with specific port and bind address
                # This will open browser at http://localhost:8080
                try:
                    creds = flow.run_local_server(
                        port=8080,
                        bind_addr='localhost',
                        authorization_prompt_message='Please visit this URL: {url}',
                        success_message='Authentication successful! You can close this window.',
                        open_browser=True
                    )
                except OSError:
                    # If port 8080 is busy, try 8081
                    creds = flow.run_local_server(
                        port=8081,
                        bind_addr='localhost',
                        authorization_prompt_message='Please visit this URL: {url}',
                        success_message='Authentication successful! You can close this window.',
                        open_browser=True
                    )
            
            # Save credentials for next run
            with open(self.token_file, 'wb') as token:
                pickle.dump(creds, token)
        
        try:
            self.service = build('gmail', 'v1', credentials=creds)
            return True
        except HttpError as error:
            print(f'An error occurred: {error}')
            return False
    
    def get_messages(self, max_results=500, query=''):
        """Fetch messages from Gmail inbox with pagination support."""
        if not self.service:
            raise Exception("Not authenticated. Call authenticate() first.")
        
        all_messages = []
        
        try:
            # Gmail API limits maxResults to 500 per request
            page_size = min(max_results, 500)
            
            results = self.service.users().messages().list(
                userId='me', 
                maxResults=page_size,
                q=query
            ).execute() # Initial request
            
            messages = results.get('messages', [])
            all_messages.extend(messages)
            
            # Handle pagination for more messages
            while 'nextPageToken' in results and len(all_messages) < max_results:
                page_token = results['nextPageToken']
                remaining = max_results - len(all_messages)
                page_size = min(remaining, 500)
                
                results = self.service.users().messages().list(
                    userId='me',
                    maxResults=page_size,
                    pageToken=page_token,
                    q=query
                ).execute()
                
                messages = results.get('messages', [])
                all_messages.extend(messages)
                
                # Safety break to avoid infinite loops
                if len(messages) == 0:
                    break
            
            # Return only the requested number
            return all_messages[:max_results]
            
        except HttpError as error:
            print(f'An error occurred: {error}')
            return []    
    
    
    def get_message_detail(self, msg_id):
        """Get detailed information about a specific message."""
        if not self.service:
            raise Exception("Not authenticated. Call authenticate() first.")
        
        try:
            message = self.service.users().messages().get(
                userId='me', 
                id=msg_id,
                format='full'
            ).execute()
            
            # Extract headers
            headers = message['payload']['headers']
            subject = next((h['value'] for h in headers if h['name'] == 'Subject'), 'No Subject')
            sender = next((h['value'] for h in headers if h['name'] == 'From'), 'Unknown')
            date = next((h['value'] for h in headers if h['name'] == 'Date'), 'Unknown')
            
            # Extract body
            body = self._get_message_body(message['payload'])
            
            # Extract links
            links = self._extract_links(body)
            
            return {
                'id': msg_id,
                'subject': subject,
                'sender': sender,
                'date': date,
                'body': body,
                'links': links,
                'snippet': message.get('snippet', '')
            }
        except HttpError as error:
            print(f'An error occurred: {error}')
            return None
    
    def _get_message_body(self, payload):
        """Extract message body from payload."""
        body = ''
        
        if 'parts' in payload:
            for part in payload['parts']:
                if part['mimeType'] == 'text/plain':
                    if 'data' in part['body']:
                        body = base64.urlsafe_b64decode(
                            part['body']['data']
                        ).decode('utf-8')
                        break
                elif part['mimeType'] == 'text/html':
                    if 'data' in part['body']:
                        body = base64.urlsafe_b64decode(
                            part['body']['data']
                        ).decode('utf-8')
        else:
            if 'body' in payload and 'data' in payload['body']:
                body = base64.urlsafe_b64decode(
                    payload['body']['data']
                ).decode('utf-8')
        
        return body
    
    def _extract_links(self, text):
        """Extract all URLs from text."""
        url_pattern = r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+'
        links = re.findall(url_pattern, text)
        return list(set(links))  # Remove duplicates
    
    def scan_inbox(self, max_results=50, use_threading=False):
        """Scan inbox and return all messages with details."""
        messages = self.get_messages(max_results=max_results)
        print(f"Found {len(messages)} message IDs")
        
        if not messages:
            print("No messages found!")
            return []
        
        detailed_messages = []
        
        if use_threading and len(messages) > 10:
            # Use threading for faster processing with many messages
            print("Using multi-threaded processing...")
            
            with ThreadPoolExecutor(max_workers=5) as executor:
                # Submit all tasks
                future_to_msg = {
                    executor.submit(self.get_message_detail, msg['id']): msg 
                    for msg in messages
                }
                
                # Process completed tasks
                for i, future in enumerate(as_completed(future_to_msg), 1):
                    print(f"Processing message {i}/{len(messages)}...", end='\r')
                    try:
                        detail = future.result()
                        if detail:
                            detailed_messages.append(detail)
                    except Exception as e:
                        print(f"\nError processing message: {e}")
        else:
            # Single-threaded processing
            for i, msg in enumerate(messages, ):
                print(f"Processing message {i}/{len(messages)}...", end='\r')
                
                detail = self.get_message_detail(msg['id'])
                if detail:
                    detailed_messages.append(detail)
        
        print(f"\nCompleted! Processed {len(detailed_messages)} messages")
        return detailed_messages


# Example usage
if __name__ == '__main__':
    client = GmailClient()
    
    if client.authenticate():
        print("Authentication successful!")
        
        # Test pagination with different limits
        print("\nTesting pagination...")
        for limit in [5, 10, 20]:
            print(f"\nRequesting {limit} messages:")
            emails = client.scan_inbox(max_results=limit)
            print(f"  ✓ Received {len(emails)} emails")
            
            if emails:
                print(f"  First email: {emails[0]['subject'][:50]}")
                print(f"  Last email: {emails[-1]['subject'][:50]}")
        
        # Full scan
        print("\n" + "="*60)
        print("Full scan with 50 emails:")
        print("="*60)
        emails = client.scan_inbox(max_results=50)
        
        print(f"\nTotal emails scanned: {len(emails)}")
        print("\nSample emails:")
        for i, email in enumerate(emails[:5], 1):
            print(f"\n{i}. Subject: {email['subject'][:60]}")
            print(f"   From: {email['sender']}")
            print(f"   Date: {email['date']}")
            print(f"   Links: {len(email['links'])}")
            if email['links']:
                print(f"   First link: {email['links'][0][:60]}")
    else:
        print("Authentication failed!")
