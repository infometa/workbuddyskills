#!/usr/bin/env python3
"""Check your AgentMail inbox."""

import json
import os
import sys
from agentmail import AgentMail

CONFIG_PATH = os.path.expanduser("~/.agentmail/config.json")

def main():
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
    
    # Get messages
    result = client.inboxes.messages.list(inbox_id=inbox_id)
    
    if result.count == 0:
        print("📭 Inbox empty - no messages")
        return
    
    print(f"📬 {result.count} message(s) in inbox:\n")
    
    for msg in result.messages:
        print(f"From: {getattr(msg, 'from_address', 'Unknown')}")
        print(f"Subject: {getattr(msg, 'subject', 'No subject')}")
        print(f"Date: {getattr(msg, 'received_at', 'Unknown')}")
        if hasattr(msg, 'snippet') and msg.snippet:
            print(f"Preview: {msg.snippet[:100]}...")
        print("-" * 40)

if __name__ == "__main__":
    main()
