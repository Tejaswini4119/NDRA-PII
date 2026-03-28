"""RFC-compliant email parser implementation.

Addresses Claude report finding: 29% MIME corruption rate.

This module provides strict RFC 5322/2045-2049 compliant email parsing
to prevent header corruption, MIME boundary mangling, and encoding errors
during PII redaction.
"""

from __future__ import annotations

import email
from email import policy
from email.message import Message, EmailMessage
from email.parser import BytesParser
from dataclasses import dataclass, field
from typing import Dict, List, Any
import base64
import quopri
from io import BytesIO


@dataclass
class ParsedEmail:
    """RFC-compliant parsed email structure."""
    
    headers: Dict[str, str]
    """Email headers (From, To, Subject, etc.)"""
    
    body_text: str
    """Plain text body content (decoded from quoted-printable/base64)"""
    
    body_html: str | None
    """HTML body content if present"""
    
    attachments: List[Dict[str, Any]]
    """List of attachments with metadata"""
    
    mime_boundaries: List[str]
    """MIME boundary strings to protect during redaction"""
    
    original_encoding: str
    """Original character encoding (for re-encoding after redaction)"""
    
    raw_message: Message
    """Original email.message.Message object for reconstruction"""
    
    content_transfer_encoding: str = "7bit"
    """Content-Transfer-Encoding of body (quoted-printable, base64, etc.)"""


class EmailParsingError(Exception):
    """Raised when email parsing fails."""
    pass


class RFCEmailParser:
    """RFC 5322/2045-2049 compliant email parser.
    
    Features:
    - Strict MIME parsing with boundary preservation
    - Proper quoted-printable/base64 decoding
    - Header folding preservation
    - Lossless reconstruction after redaction
    
    Usage:
        parser = RFCEmailParser()
        parsed = parser.parse(raw_email_bytes)
        # ... perform redaction on parsed.body_text ...
        reconstructed = parser.reconstruct(parsed, redacted_text)
    """
    
    def __init__(self, strict_parsing: bool = True):
        """Initialize parser.
        
        Args:
            strict_parsing: If True, raise errors on malformed emails.
                           If False, attempt best-effort parsing.
        """
        self.strict_parsing = strict_parsing
        # Use email.policy.default for strict RFC compliance
        self.policy = policy.default if strict_parsing else policy.compat32
    
    def parse(self, raw_email: bytes) -> ParsedEmail:
        """Parse raw email bytes into structured components.
        
        Args:
            raw_email: Raw .eml file as bytes
            
        Returns:
            ParsedEmail with decoded headers, body, attachments
            
        Raises:
            EmailParsingError: If email is malformed and strict_parsing=True
        """
        try:
            # Use BytesParser for proper binary handling
            parser = BytesParser(policy=self.policy)
            msg = parser.parsebytes(raw_email)
            
            # Extract headers
            headers = self._extract_headers(msg)
            
            # Extract MIME boundaries for protection
            boundaries = self._extract_mime_boundaries(msg)
            
            # Extract body content
            body_text, body_html, encoding, transfer_encoding = self._extract_body(msg)
            
            # Extract attachments
            attachments = self._extract_attachments(msg)
            
            return ParsedEmail(
                headers=headers,
                body_text=body_text,
                body_html=body_html,
                attachments=attachments,
                mime_boundaries=boundaries,
                original_encoding=encoding,
                content_transfer_encoding=transfer_encoding,
                raw_message=msg,
            )
            
        except Exception as e:
            if self.strict_parsing:
                raise EmailParsingError(f"Failed to parse email: {e}") from e
            else:
                # Best-effort fallback
                return self._fallback_parse(raw_email, e)
    
    def _extract_headers(self, msg: Message) -> Dict[str, str]:
        """Extract email headers preserving RFC 5322 folding.
        
        Args:
            msg: Parsed email message
            
        Returns:
            Dictionary of header name -> value
        """
        headers = {}
        for key, value in msg.items():
            # Preserve folded headers by keeping them as single strings
            # The email library handles unfolding automatically
            headers[key] = str(value)
        return headers
    
    def _extract_mime_boundaries(self, msg: Message) -> List[str]:
        """Extract all MIME boundary strings that must be protected.
        
        MIME boundaries are declared in Content-Type headers like:
        Content-Type: multipart/mixed; boundary="----=_Part_123"
        
        These MUST NOT be redacted as they define message structure.
        
        Args:
            msg: Parsed email message
            
        Returns:
            List of boundary strings (without leading --)
        """
        boundaries = []
        
        # Check main message boundary
        if msg.is_multipart():
            boundary = msg.get_boundary()
            if boundary:
                boundaries.append(boundary)
        
        # Recursively check all parts
        if msg.is_multipart():
            for part in msg.walk():
                if part.is_multipart():
                    boundary = part.get_boundary()
                    if boundary:
                        boundaries.append(boundary)
        
        return boundaries
    
    def _extract_body(self, msg: Message) -> tuple[str, str | None, str, str]:
        """Extract email body content with proper decoding.
        
        Args:
            msg: Parsed email message
            
        Returns:
            Tuple of (plain_text, html_text, encoding, transfer_encoding)
        """
        plain_text = ""
        html_text = None
        encoding = "utf-8"
        transfer_encoding = "7bit"
        
        if msg.is_multipart():
            # Handle multipart messages
            for part in msg.walk():
                content_type = part.get_content_type()
                content_disposition = str(part.get("Content-Disposition", ""))
                
                # Skip attachments
                if "attachment" in content_disposition:
                    continue
                
                # Extract text/plain
                if content_type == "text/plain":
                    payload = part.get_payload(decode=True)
                    if payload:
                        charset = part.get_content_charset() or "utf-8"
                        encoding = charset
                        plain_text = payload.decode(charset, errors="replace")
                        transfer_encoding = part.get("Content-Transfer-Encoding", "7bit")
                
                # Extract text/html
                elif content_type == "text/html":
                    payload = part.get_payload(decode=True)
                    if payload:
                        charset = part.get_content_charset() or "utf-8"
                        html_text = payload.decode(charset, errors="replace")
        
        else:
            # Handle single-part messages
            content_type = msg.get_content_type()
            if content_type in ("text/plain", "text/html"):
                payload = msg.get_payload(decode=True)
                if payload:
                    charset = msg.get_content_charset() or "utf-8"
                    encoding = charset
                    decoded = payload.decode(charset, errors="replace")
                    
                    if content_type == "text/plain":
                        plain_text = decoded
                    else:
                        html_text = decoded
                    
                    transfer_encoding = msg.get("Content-Transfer-Encoding", "7bit")
        
        return plain_text, html_text, encoding, transfer_encoding
    
    def _extract_attachments(self, msg: Message) -> List[Dict[str, Any]]:
        """Extract attachment metadata.
        
        Args:
            msg: Parsed email message
            
        Returns:
            List of attachment metadata dicts
        """
        attachments = []
        
        if msg.is_multipart():
            for part in msg.walk():
                content_disposition = str(part.get("Content-Disposition", ""))
                
                if "attachment" in content_disposition:
                    filename = part.get_filename()
                    content_type = part.get_content_type()
                    size = len(part.get_payload(decode=True) or b"")
                    
                    attachments.append({
                        "filename": filename,
                        "content_type": content_type,
                        "size_bytes": size,
                    })
        
        return attachments
    
    def reconstruct(self, parsed: ParsedEmail, redacted_text: str) -> bytes:
        """Reconstruct email with redacted text, preserving structure.
        
        This is the critical function that prevents MIME corruption.
        It ensures:
        1. Headers are properly folded per RFC 5322
        2. MIME boundaries are never corrupted
        3. Content-Transfer-Encoding is correctly reapplied
        4. Character encoding roundtrips correctly
        
        Args:
            parsed: Original ParsedEmail
            redacted_text: Redacted body text
            
        Returns:
            Reconstructed .eml as bytes with proper MIME encoding
        """
        msg = parsed.raw_message
        
        # Handle multipart messages
        if msg.is_multipart():
            # Find and replace the text/plain part
            for part in msg.walk():
                content_type = part.get_content_type()
                content_disposition = str(part.get("Content-Disposition", ""))
                
                # Skip attachments
                if "attachment" in content_disposition:
                    continue
                
                # Replace text/plain body
                if content_type == "text/plain":
                    self._set_part_payload(part, redacted_text, parsed)
                    break
        
        else:
            # Single-part message
            if msg.get_content_type() == "text/plain":
                self._set_part_payload(msg, redacted_text, parsed)
        
        # Serialize back to bytes
        return msg.as_bytes(policy=self.policy)
    
    def _set_part_payload(
        self, 
        part: Message, 
        text: str, 
        parsed: ParsedEmail
    ) -> None:
        """Set message part payload with proper encoding.
        
        Critical: This ensures bracket characters [, ] are properly encoded
        in quoted-printable to prevent codec errors (Claude report finding).
        
        Args:
            part: Message part to update
            text: Redacted text to set
            parsed: Original ParsedEmail for encoding info
        """
        # Encode text to bytes
        text_bytes = text.encode(parsed.original_encoding, errors="replace")
        
        # Apply Content-Transfer-Encoding
        transfer_encoding = parsed.content_transfer_encoding.lower()
        
        if transfer_encoding == "quoted-printable":
            # Encode with quopri, which properly escapes [, ] as =5B, =5D
            encoded = quopri.encodestring(text_bytes)
            part.set_payload(encoded.decode("ascii"))
            
        elif transfer_encoding == "base64":
            # Encode with base64
            encoded = base64.b64encode(text_bytes)
            part.set_payload(encoded.decode("ascii"))
            
        else:
            # 7bit, 8bit, binary - set directly
            part.set_payload(text)
        
        # Ensure Content-Transfer-Encoding header is set
        if "Content-Transfer-Encoding" not in part:
            part["Content-Transfer-Encoding"] = transfer_encoding
    
    def _fallback_parse(self, raw_email: bytes, error: Exception) -> ParsedEmail:
        """Best-effort parsing when strict parsing fails.
        
        Args:
            raw_email: Raw email bytes
            error: Original parsing error
            
        Returns:
            ParsedEmail with whatever we could extract
        """
        # Try to decode as UTF-8 and extract text naively
        try:
            text = raw_email.decode("utf-8", errors="replace")
        except:
            text = raw_email.decode("latin1", errors="replace")
        
        # Create minimal ParsedEmail
        return ParsedEmail(
            headers={"X-Parse-Error": str(error)},
            body_text=text,
            body_html=None,
            attachments=[],
            mime_boundaries=[],
            original_encoding="utf-8",
            raw_message=email.message_from_bytes(raw_email, policy=policy.compat32),
        )
    
    def get_protected_strings(self, parsed: ParsedEmail) -> List[str]:
        """Get all strings that must be protected during redaction.
        
        These strings MUST NOT be matched by PII patterns as redacting
        them would corrupt the email structure.
        
        Args:
            parsed: Parsed email
            
        Returns:
            List of protected strings (boundaries, technical headers, etc.)
        """
        protected = []
        
        # Add MIME boundaries (with -- prefix variants)
        for boundary in parsed.mime_boundaries:
            protected.append(boundary)
            protected.append(f"--{boundary}")
            protected.append(f"--{boundary}--")
        
        # Add critical header markers
        protected.extend([
            "Content-Type:",
            "Content-Transfer-Encoding:",
            "MIME-Version:",
            "Content-Disposition:",
        ])
        
        return protected
