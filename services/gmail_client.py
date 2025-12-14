import imaplib
import email
from email.header import decode_header
from typing import List, Dict, Tuple

from utils.logger import logger


class GmailClient:
    """Client for interacting with Gmail via IMAP."""
    
    def __init__(self, email_address: str, password: str):
        """Initialize Gmail client with credentials.
        
        Args:
            email_address: Gmail email address
            password: Gmail app-specific password
        """
        self.email_address = email_address
        self.password = password
        self.imap = None
        self._connect()
    
    def _connect(self) -> None:
        """Connect to Gmail IMAP server."""
        if not self.email_address or not self.password:
            raise ValueError("Email and password are required")
        
        try:
            self.imap = imaplib.IMAP4_SSL("imap.gmail.com")
            self.imap.login(self.email_address, self.password)
        except imaplib.IMAP4.error as exc:
            logger.error(f"IMAP authentication failed: {exc}")
            raise
        except Exception as exc:
            logger.error(f"IMAP connection error: {exc}")
            raise
    
    def fetch_messages(self, query: str = 'ALL', max_results: int = 100) -> List[Dict]:
        """Fetch messages from Gmail.
        
        Args:
            query: IMAP search query (default: 'ALL')
            max_results: Maximum number of messages to fetch
            
        Returns:
            List of message dictionaries
        """
        if not self.imap:
            raise ValueError("Gmail connection not established")
        
        safe_max_results = max(1, min(max_results, 500))
        
        try:
            select_status, _ = self.imap.select("INBOX")
            if select_status != "OK":
                return []
            
            status, message_ids = self.imap.search(None, query)
            if status != "OK" or not message_ids or not message_ids[0]:
                return []
        except Exception as exc:
            logger.error(f"IMAP search error: {exc}")
            return []
        
        message_id_list = message_ids[0].split()
        message_id_list.reverse()
        
        messages: List[Dict] = []
        for msg_id in message_id_list[:safe_max_results]:
            try:
                fetch_status, msg_data = self.imap.fetch(msg_id, "(RFC822)")
                if fetch_status != "OK":
                    continue
                
                for response_part in msg_data:
                    if isinstance(response_part, tuple):
                        msg = email.message_from_bytes(response_part[1])
                        messages.append({
                            'id': msg_id.decode(),
                            'raw_message': msg
                        })
            except Exception as exc:
                logger.error(f"Failed to fetch or parse message {msg_id}: {exc}")
                continue
        
        return messages
    
    
    def extract_message_data(self, message: Dict) -> Dict:
        """Extract relevant data from a Gmail message.
        
        Args:
            message: Message dictionary with raw_message
            
        Returns:
            Dictionary with extracted message data
        """
        msg = message.get('raw_message')
        
        subject = self._decode_header(msg.get("Subject", ""))
        from_email = self._decode_header(msg.get("From", ""))
        date = msg.get("Date", "")
        
        body = self._extract_body(msg)
        snippet = body[:200] if body else ""
        
        attachments = self._extract_attachments(msg)
        
        return {
            'id': message.get('id'),
            'thread_id': '',
            'subject': subject,
            'from': from_email,
            'date': date,
            'body': body,
            'snippet': snippet,
            'attachments': attachments,
        }
    
    def _decode_header(self, header: str) -> str:
        """Decode email header.
        
        Args:
            header: Email header string
            
        Returns:
            Decoded header string
        """
        if not header:
            return ""
        
        decoded_parts = decode_header(header)
        decoded_header = ""
        
        for part, encoding in decoded_parts:
            if isinstance(part, bytes):
                if encoding:
                    decoded_header += part.decode(encoding, errors='ignore')
                else:
                    decoded_header += part.decode('utf-8', errors='ignore')
            else:
                decoded_header += part
        
        return decoded_header
    
    def _extract_body(self, msg) -> str:
        if msg.is_multipart():
            for part in msg.walk():
                if part.get_content_maintype() == "multipart":
                    continue
                if "attachment" in str(part.get("Content-Disposition", "")).lower():
                    continue
                if part.get_content_type() == "text/plain":
                    payload = part.get_payload(decode=True) or b""
                    return payload.decode("utf-8", errors="ignore")
            for part in msg.walk():
                if part.get_content_type() == "text/html":
                    payload = part.get_payload(decode=True) or b""
                    return payload.decode("utf-8", errors="ignore")
            return ""
        payload = msg.get_payload(decode=True) or b""
        return payload.decode("utf-8", errors="ignore") if isinstance(payload, (bytes, bytearray)) else str(payload)
    
    def _extract_attachments(self, msg) -> List[Tuple[str, bytes]]:
        attachments: List[Tuple[str, bytes]] = []
        
        if msg.is_multipart():
            for part in msg.walk():
                content_disposition = str(part.get("Content-Disposition", ""))
                content_type = part.get_content_type()
                
                if "attachment" in content_disposition or content_type == "application/pdf":
                    filename = part.get_filename()
                    if not filename:
                        continue
                    
                    filename = self._decode_header(filename)
                    if not filename.lower().endswith('.pdf'):
                        continue
                    
                    try:
                        payload = part.get_payload(decode=True)
                        if payload:
                            attachments.append((filename, payload))
                    except Exception as exc:
                        logger.warning(f"Failed to decode attachment {filename}: {exc}")
                        continue
        
        return attachments
    
    def close(self) -> None:
        """Close IMAP connection."""
        if self.imap:
            try:
                self.imap.close()
                self.imap.logout()
            except:
                pass
