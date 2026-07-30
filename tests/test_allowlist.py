"""
Tests for the AegisOps Shell Agent command allowlist.

The allowlist is the security boundary:
- Only approved diagnostic commands are allowed.
- Parameters must pass validation.
- Shell injection must be blocked.
"""


import pytest

from sandbox.allowlist import (
    build_command,
    CommandNotAllowedError,
)



# ============================================================
# Network Tests
# ============================================================

def test_ping_with_valid_target():

    cmd = build_command(
        "ping",
        target="localhost"
    )

    assert cmd == "ping -c 4 localhost"



def test_ping_rejects_shell_injection_attempt():

    with pytest.raises(CommandNotAllowedError):

        build_command(
            "ping",
            target="localhost; rm -rf /"
        )



# ============================================================
# Allowlist Boundary Tests
# ============================================================

def test_command_not_in_allowlist_raises():

    with pytest.raises(CommandNotAllowedError):

        build_command(
            "rm -rf /",
            target=None
        )



def test_unknown_command_blocked():

    with pytest.raises(CommandNotAllowedError):

        build_command(
            "delete_logs",
            target=None
        )



# ============================================================
# Commands Without Parameters
# ============================================================

def test_disk_usage_command():

    cmd = build_command(
        "disk_usage"
    )

    assert cmd == "df -h"



def test_failed_login_command():

    cmd = build_command(
        "failed_logins"
    )

    assert (
        "Failed password"
        in cmd
    )



# ============================================================
# Service Validation
# ============================================================

def test_service_status_valid():

    cmd = build_command(
        "service_status",
        target="nginx"
    )

    assert (
        cmd ==
        "systemctl status nginx"
    )



def test_service_status_rejects_invalid_service_name():

    with pytest.raises(CommandNotAllowedError):

        build_command(
            "service_status",
            target="nginx && curl evil.com"
        )



# ============================================================
# User Validation
# ============================================================

def test_faillock_valid_user():

    cmd = build_command(
        "faillock",
        target="admin"
    )

    assert (
        cmd ==
        "faillock --user admin"
    )



def test_faillock_blocks_injection():

    with pytest.raises(CommandNotAllowedError):

        build_command(
            "faillock",
            target="admin;cat /etc/passwd"
        )
