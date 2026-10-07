"""Unit tests for the create_admin.py CLI script."""

from unittest.mock import patch
import sys
import pytest
from app import db
from app.security import verify_password
import create_admin


def test_create_admin_script_interactive(sqlite_test_db, monkeypatch):
    """Test creating an administrator via create_admin.main() with interactive terminal prompts."""
    inputs = [
        "Super Administrator",   # Name
        "9998887766",            # Phone
        "superadmin@agripredict.in",  # Email
        "Pune",                  # District
        "Haveli",                # Village
        "en",                    # Language
        "n",                     # Do you want to see password characters? (n = hidden)
    ]
    passwords = [
        "adminSecret123",        # Password
        "adminSecret123",        # Confirm Password
    ]

    monkeypatch.setattr("builtins.input", lambda prompt="": inputs.pop(0))
    monkeypatch.setattr("getpass.getpass", lambda prompt="": passwords.pop(0))
    monkeypatch.setattr("sys.argv", ["create_admin.py"])

    # Execute main()
    create_admin.main()

    # Verify admin in database
    admin = db.fetch_one("SELECT * FROM farmers WHERE phone = %s", ("9998887766",))
    assert admin is not None
    assert admin["name"] == "Super Administrator"
    assert admin["email"] == "superadmin@agripredict.in"
    assert admin["role"] == "admin"
    assert admin["is_active"] == 1
    assert verify_password("adminSecret123", admin["password_hash"])


def test_create_admin_script_cli_flags(sqlite_test_db, monkeypatch):
    """Test creating an administrator using non-interactive command-line flags."""
    test_args = [
        "create_admin.py",
        "--name", "CLI Administrator",
        "--phone", "9998887777",
        "--email", "cliadmin@agripredict.in",
        "--password", "cliAdminPass123",
        "--district", "Nagpur",
        "--village", "Katol",
        "--language", "mr",
    ]
    monkeypatch.setattr("sys.argv", test_args)

    create_admin.main()

    admin = db.fetch_one("SELECT * FROM farmers WHERE phone = %s", ("9998887777",))
    assert admin is not None
    assert admin["name"] == "CLI Administrator"
    assert admin["phone"] == "9998887777"
    assert admin["language"] == "mr"
    assert admin["role"] == "admin"
    assert verify_password("cliAdminPass123", admin["password_hash"])
