#!/usr/bin/env python3
"""Send email from your AgentMail inbox."""

import json
import os
import sys
import argparse
from agentmail import AgentMail

CONFIG_PATH = os.path.expanduser("~/.agentmail/config.json")

def main():
    parser = argparse.ArgumentParser(description="Send email from your AgentMail inbox")
    parser.add_argument("--to", required=True, help="Recipient email address")
    parser.add_argument("--subject", required=True, help="Email subject")
    parser.add_argument("--body", required=True, help="Email body text")
    args = parser.parse_args()
    
    # Check config exists
    if not os.path.exists(CONFIG_PATH):
        print(f"❌ Config not found at {CONFIG_PATH}")
        print("Run setup first. See SKILL.md for instructions.")
        sys.exit(1)
    
    # Load config
    with open(CONFIG_PATH) as f:
        config = json.load(f)
    
    api_key = config.get('apiKey')
    inbox_id = config.get('email')
    
    if not api_key or not inbox_id:
        print("❌ Config missing 'apiKey' or 'email' field")
        sys.exit(1)
    
    client = AgentMail(api_key=api_key)
    
    # Send email
    try:
        result = client.inboxes.messages.send(
            inbox_id=inbox_id,
            to=args.to,
            subject=args.subject,
            text=args.body
        )
        print(f"✅ Email sent to {args.to}")
        print(f"Subject: {args.subject}")
    except Exception as e:
        print(f"❌ Failed to send email: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
