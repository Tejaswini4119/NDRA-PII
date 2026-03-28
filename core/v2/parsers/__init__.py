"""Email parsers for v2 architecture."""

from .rfc_email_parser import RFCEmailParser, ParsedEmail, EmailParsingError

__all__ = ["RFCEmailParser", "ParsedEmail", "EmailParsingError"]
