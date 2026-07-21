#!/usr/bin/env python3
"""
Email Sender Skill for OpenClaw
Supports sending emails with attachments via SMTP
"""

import os
import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from typing import Optional, List
import json
import sys

class EmailSender:
    def __init__(self, config_path: str = None):
        """Initialize email sender with configuration"""
        self.config = self.load_config(config_path)
        
    def load_config(self, config_path: str = None) -> dict:
        """Load email configuration from file or environment variables"""
        config = {}
        
        # Try to load from config file
        if config_path and os.path.exists(config_path):
            try:
                with open(config_path, 'r') as f:
                    config = json.load(f)
            except Exception as e:
                print(f"Error loading config file: {e}")
        
        # Fall back to environment variables
        env_config = {
            'smtp_server': os.getenv('SMTP_SERVER'),
            'smtp_port': int(os.getenv('SMTP_PORT', '587')),
            'username': os.getenv('EMAIL_USERNAME'),
            'password': os.getenv('EMAIL_PASSWORD'),
            'sender_name': os.getenv('EMAIL_SENDER_NAME', 'OpenClaw Assistant'),
            'use_tls': os.getenv('EMAIL_USE_TLS', 'true').lower() == 'true',
            'use_ssl': os.getenv('EMAIL_USE_SSL', 'false').lower() == 'true'
        }
        
        # Merge configs (environment variables override file config)
        for key, value in env_config.items():
            if value is not None:
                config[key] = value
        
        return config
    
    def validate_config(self) -> bool:
        """Validate that required configuration is present"""
        required = ['smtp_server', 'smtp_port', 'username', 'password']
        for key in required:
            if key not in self.config or not self.config[key]:
                print(f"Missing required configuration: {key}")
                return False
        return True
    
    def send_email(
        self,
        to_email: str,
        subject: str,
        body: str,
        attachments: List[str] = None,
        cc: List[str] = None,
        bcc: List[str] = None,
        html_body: str = None
    ) -> dict:
        """
        Send an email with optional attachments
        
        Args:
            to_email: Recipient email address(es) - can be string or list
            subject: Email subject
            body: Plain text email body
            attachments: List of file paths to attach
            cc: List of CC email addresses
            bcc: List of BCC email addresses
            html_body: HTML version of email body (optional)
            
        Returns:
            Dictionary with success status and message
        """
        if not self.validate_config():
            return {"success": False, "error": "Invalid email configuration"}
        
        try:
            # Create message
            msg = MIMEMultipart('alternative')
            msg['From'] = f"{self.config.get('sender_name', 'OpenClaw')} <{self.config['username']}>"
            msg['To'] = to_email if isinstance(to_email, str) else ', '.join(to_email)
            msg['Subject'] = subject
            
            if cc:
                msg['Cc'] = ', '.join(cc)
            
            # Add recipients for BCC
            all_recipients = []
            if isinstance(to_email, str):
                all_recipients.append(to_email)
            else:
                all_recipients.extend(to_email)
            
            if cc:
                all_recipients.extend(cc)
            if bcc:
                all_recipients.extend(bcc)
            
            # Add text body
            msg.attach(MIMEText(body, 'plain'))
            
            # Add HTML body if provided
            if html_body:
                msg.attach(MIMEText(html_body, 'html'))
            
            # Add attachments
            if attachments:
                for attachment_path in attachments:
                    if os.path.exists(attachment_path):
                        self._add_attachment(msg, attachment_path)
                    else:
                        print(f"Warning: Attachment not found: {attachment_path}")
            
            # Connect to SMTP server
            context = ssl.create_default_context()
            
            if self.config.get('use_ssl', False):
                # SSL connection
                server = smtplib.SMTP_SSL(
                    self.config['smtp_server'],
                    self.config['smtp_port'],
                    context=context
                )
            else:
                # TLS connection (default)
                server = smtplib.SMTP(
                    self.config['smtp_server'],
                    self.config['smtp_port']
                )
                if self.config.get('use_tls', True):
                    server.starttls(context=context)
            
            # Login and send
            server.login(self.config['username'], self.config['password'])
            server.send_message(msg, from_addr=self.config['username'], to_addrs=all_recipients)
            server.quit()
            
            return {
                "success": True,
                "message": f"Email sent successfully to {to_email}",
                "subject": subject,
                "attachments": len(attachments) if attachments else 0
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "subject": subject
            }
    
    def _add_attachment(self, msg: MIMEMultipart, filepath: str):
        """Add a file attachment to the email"""
        filename = os.path.basename(filepath)
        
        with open(filepath, 'rb') as f:
            part = MIMEBase('application', 'octet-stream')
            part.set_payload(f.read())
        
        encoders.encode_base64(part)
        part.add_header(
            'Content-Disposition',
            f'attachment; filename="{filename}"'
        )
        msg.attach(part)
    
    def send_test_email(self, to_email: str = None) -> dict:
        """Send a test email to verify configuration"""
        test_to = to_email or self.config['username']
        subject = "Test Email from OpenClaw"
        body = """This is a test email sent from your OpenClaw assistant.

If you're receiving this, your email configuration is working correctly!

Best regards,
OpenClaw Assistant"""
        
        return self.send_email(test_to, subject, body)

def main():
    """Command-line interface for email sending"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Send email with attachments')
    parser.add_argument('--to', required=True, help='Recipient email address')
    parser.add_argument('--subject', required=True, help='Email subject')
    parser.add_argument('--body', required=True, help='Email body text')
    parser.add_argument('--attachment', action='append', help='Attachment file path (can be used multiple times)')
    parser.add_argument('--config', help='Path to configuration file')
    parser.add_argument('--test', action='store_true', help='Send test email')
    
    args = parser.parse_args()
    
    sender = EmailSender(args.config)
    
    if args.test:
        result = sender.send_test_email(args.to)
    else:
        result = sender.send_email(
            to_email=args.to,
            subject=args.subject,
            body=args.body,
            attachments=args.attachment
        )
    
    print(json.dumps(result, indent=2))
    sys.exit(0 if result['success'] else 1)

if __name__ == '__main__':
    main()