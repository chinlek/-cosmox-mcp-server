#!/usr/bin/env python3
"""
Token refresh helper for COSMOX MCP.

This script can be run hourly via cron to refresh your COSMOX access token.
It requires you to manually log in once and set up the browser extension or
use the instructions below.

Usage:
    # Manual refresh (get fresh token from browser)
    /auto/smartdev/bin/python3.10 /nobackup/lcv/cosmox-mcp-server/refresh_token.py --manual

    # Cron job (every 55 minutes to refresh before 1-hour expiry)
    55 * * * * /auto/smartdev/bin/python3.10 /nobackup/lcv/cosmox-mcp-server/refresh_token.py
"""

import sys
import os
import argparse
import json
import base64
import time
from datetime import datetime, timezone
from pathlib import Path


def get_token_from_env():
    """Read token from .env file."""
    env_file = Path('/nobackup/lcv/cosmox-mcp-server/.env')
    if not env_file.exists():
        return None

    with open(env_file, 'r') as f:
        for line in f:
            if line.startswith('COSMOX_ACCESS_TOKEN='):
                return line.split('=', 1)[1].strip()
    return None


def check_token_validity(token):
    """Check if token is still valid and how much time is left."""
    if not token or ':' not in token:
        return None, None, None

    try:
        parts = token.split(':')
        first_jwt = parts[0]

        # Extract payload
        payload = first_jwt.split('.')[1]
        padding = 4 - len(payload) % 4
        if padding != 4:
            payload += '=' * padding

        decoded = base64.urlsafe_b64decode(payload)
        data = json.loads(decoded)

        exp = data.get('exp')
        iat = data.get('iat')
        now = int(time.time())

        exp_time = datetime.fromtimestamp(exp, tz=timezone.utc)
        time_left = exp - now
        is_valid = time_left > 0

        return is_valid, exp_time, time_left
    except Exception as e:
        print(f"Error checking token: {e}")
        return None, None, None


def update_token_in_env(new_token):
    """Update token in .env file."""
    env_file = Path('/nobackup/lcv/cosmox-mcp-server/.env')

    if not env_file.exists():
        print(f"Error: .env file not found at {env_file}")
        return False

    # Read existing content
    content = env_file.read_text()

    # Replace token line
    lines = []
    for line in content.split('\n'):
        if line.startswith('COSMOX_ACCESS_TOKEN='):
            lines.append(f'COSMOX_ACCESS_TOKEN={new_token}')
        else:
            lines.append(line)

    # Write back
    env_file.write_text('\n'.join(lines))
    return True


def manual_refresh():
    """Prompt user to manually refresh token."""
    print("=" * 70)
    print("🔄 Manual Token Refresh")
    print("=" * 70)
    print()
    print("Steps to get a fresh token:")
    print()
    print("1. Open browser and go to: https://cosmosx.cisco.com")
    print("2. Log in with your SSO credentials")
    print("3. Wait for page to fully load (5-10 seconds)")
    print("4. Open Developer Tools (F12)")
    print("5. Go to: Application → Storage → localStorage")
    print("6. Find 'access_token' entry")
    print("7. Copy the ENTIRE token value (long string)")
    print("8. Paste it below:")
    print()

    token = input("Enter new token: ").strip()

    if not token or ':' not in token:
        print("❌ Invalid token format. Token should contain a colon (:)")
        return False

    is_valid, exp_time, time_left = check_token_validity(token)

    if not is_valid:
        print("❌ Token is already expired or invalid!")
        return False

    hours_left = time_left / 3600
    print()
    print(f"✅ Token is valid for {hours_left:.1f} hours")
    print(f"   Expires at: {exp_time.strftime('%Y-%m-%d %H:%M:%S UTC')}")
    print()

    confirm = input("Update .env file with this token? (y/n): ").strip().lower()
    if confirm == 'y':
        if update_token_in_env(token):
            print("✅ Token updated in .env file!")
            return True
        else:
            print("❌ Failed to update .env file")
            return False

    return False


def auto_refresh():
    """Auto-refresh mode (checks if token needs refresh, for cron)."""
    token = get_token_from_env()

    if not token:
        print(f"{datetime.now().isoformat()} - Error: No token found in .env")
        return False

    is_valid, exp_time, time_left = check_token_validity(token)

    if is_valid and time_left > 1800:  # More than 30 minutes left
        print(f"{datetime.now().isoformat()} - Token still valid ({int(time_left/60)} min left)")
        return True

    if time_left and time_left <= 1800:
        print(f"{datetime.now().isoformat()} - ⚠️  Token expiring soon ({int(time_left/60)} min left)")
        print("   Run: python3.10 /nobackup/lcv/cosmox-mcp-server/refresh_token.py --manual")
        return False

    print(f"{datetime.now().isoformat()} - ❌ Token expired!")
    return False


def main():
    parser = argparse.ArgumentParser(description='COSMOX Token Refresh Helper')
    parser.add_argument('--manual', action='store_true', help='Manual token refresh')
    parser.add_argument('--check', action='store_true', help='Check token status only')
    args = parser.parse_args()

    if args.manual:
        manual_refresh()
    elif args.check:
        token = get_token_from_env()
        if token:
            is_valid, exp_time, time_left = check_token_validity(token)
            if is_valid:
                hours = time_left / 3600
                print(f"✅ Token is valid - {hours:.1f} hours remaining")
                print(f"   Expires: {exp_time.strftime('%Y-%m-%d %H:%M:%S UTC')}")
            else:
                print(f"❌ Token expired at {exp_time.strftime('%Y-%m-%d %H:%M:%S UTC')}")
        else:
            print("❌ No token found in .env")
    else:
        # Cron mode (silent unless there's an issue)
        auto_refresh()


if __name__ == '__main__':
    main()
