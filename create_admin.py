#!/usr/bin/env python3
"""Interactive & CLI script to create an AgriPredict administrator user."""

import argparse
import getpass
import sys
from app import db
from app.security import hash_password


def prompt_input(prompt_text: str, default: str = "") -> str:
    """Helper to prompt for input with an optional default value."""
    if default:
        raw = input(f"{prompt_text} [{default}]: ").strip()
        return raw if raw else default
    while True:
        raw = input(f"{prompt_text}: ").strip()
        if raw:
            return raw
        print("  Error: This field cannot be empty.")


def get_password_input(show_chars: bool = False) -> str:
    """Collect and confirm password, supporting masked or visible input."""
    while True:
        if show_chars:
            password = input("Enter Admin Password (visible): ").strip()
        else:
            print("(Note: For security, characters will NOT appear on screen while you type. Simply type and hit Enter)")
            try:
                password = getpass.getpass("Enter Admin Password (min 6 chars): ")
            except Exception:
                # Terminal doesn't support getpass, fallback to visible input
                print("Notice: Hidden input not supported in this terminal, using standard prompt.")
                password = input("Enter Admin Password (min 6 chars): ").strip()

        if len(password) < 6:
            print("  Error: Password must be at least 6 characters long.\n")
            continue

        if show_chars:
            confirm = input("Confirm Admin Password (visible): ").strip()
        else:
            try:
                confirm = getpass.getpass("Confirm Admin Password: ")
            except Exception:
                confirm = input("Confirm Admin Password: ").strip()

        if password != confirm:
            print("  Error: Passwords do not match. Please try again.\n")
            continue

        return password


def main():
    parser = argparse.ArgumentParser(description="Create an AgriPredict administrator account.")
    parser.add_argument("--name", help="Admin full name")
    parser.add_argument("--phone", help="Admin mobile phone number (10-15 digits)")
    parser.add_argument("--email", help="Admin email address (optional)")
    parser.add_argument("--password", help="Admin password (min 6 characters)")
    parser.add_argument("--district", help="District name (optional)")
    parser.add_argument("--village", help="Village name (optional)")
    parser.add_argument("--language", choices=["en", "mr", "hi"], default="en", help="Language code (en, mr, hi)")
    parser.add_argument("--visible-password", action="store_true", help="Show password on screen while typing")

    args = parser.parse_args()

    print("=" * 60)
    print("        AgriPredict - Create Administrator Account")
    print("=" * 60)
    print("This script will create a new administrator in the 'farmers' table.")
    print("Role will be set to 'admin' and is_active will be set to 1.\n")

    # 1. Collect name
    name = args.name or prompt_input("Enter Admin Full Name", default="System Administrator")

    # 2. Collect phone
    raw_phone = args.phone or prompt_input("Enter Mobile Phone (10-15 digits)")
    phone = raw_phone.replace(" ", "").replace("-", "")
    if len(phone) < 10:
        print("Error: Phone number must have at least 10 digits.")
        sys.exit(1)

    # 3. Collect email
    if args.email is not None:
        email = args.email.strip() or None
    else:
        email_input = input("Enter Email Address (optional, press Enter to skip): ").strip()
        email = email_input if email_input else None

    # 4. Collect district & village
    district = args.district if args.district is not None else (input("Enter District (optional): ").strip() or None)
    village = args.village if args.village is not None else (input("Enter Village (optional): ").strip() or None)

    # 5. Collect language
    if args.language and args.name:  # Passed via CLI
        lang_choice = args.language
    else:
        raw_lang = input("Enter Language ('en', 'mr', 'hi') [en]: ").strip().lower() or "en"
        lang_choice = raw_lang if raw_lang in ("en", "mr", "hi") else "en"

    # 6. Collect password
    if args.password:
        password = args.password
        if len(password) < 6:
            print("Error: Password must be at least 6 characters long.")
            sys.exit(1)
    else:
        print()
        show_visible = args.visible_password
        if not show_visible:
            mode_choice = input("Do you want to see password characters as you type? (y/N): ").strip().lower()
            if mode_choice in ("y", "yes"):
                show_visible = True
        password = get_password_input(show_chars=show_visible)

    # 7. Check for existing phone / email in database
    print("\nConnecting to database...")
    try:
        existing_phone = db.fetch_one("SELECT farmer_id FROM farmers WHERE phone = %s", (phone,))
        if existing_phone:
            print(f"Error: A user with phone number '{phone}' already exists.")
            sys.exit(1)

        if email:
            existing_email = db.fetch_one("SELECT farmer_id FROM farmers WHERE email = %s", (email,))
            if existing_email:
                print(f"Error: A user with email address '{email}' already exists.")
                sys.exit(1)
    except Exception as e:
        print(f"Database error while checking uniqueness: {e}")
        print("Please ensure your MySQL server is running and .env settings are correct.")
        sys.exit(1)

    # 8. Hash password with bcrypt
    print("Hashing password with bcrypt...")
    hashed_password = hash_password(password)

    # 9. Insert into database using parameterized query
    insert_query = """
        INSERT INTO farmers (
            name, phone, email, password_hash, district, village, language, role, is_active
        ) VALUES (
            %s, %s, %s, %s, %s, %s, %s, 'admin', 1
        )
    """

    try:
        admin_id = db.execute_insert(
            insert_query,
            (name, phone, email, hashed_password, district, village, lang_choice),
        )
        print("\n" + "=" * 60)
        print("SUCCESS! Administrator account created successfully.")
        print(f"  Admin ID : {admin_id}")
        print(f"  Name     : {name}")
        print(f"  Phone    : {phone}")
        print(f"  Email    : {email or 'None'}")
        print(f"  Role     : admin")
        print(f"  Language : {lang_choice}")
        print("=" * 60)
    except Exception as e:
        print(f"Failed to create admin in database: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
