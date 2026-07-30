"""
The command allowlist for the Shell Agent.

The LLM never generates shell commands.
It only selects an allowlisted command name and, if required,
provides a validated parameter.

All commands are read-only diagnostics.
"""

import re

# -------------------------------------------------------------
# Validation patterns
# -------------------------------------------------------------

HOST_PATTERN = re.compile(r"^[a-zA-Z0-9.\-]+$")
SERVICE_PATTERN = re.compile(r"^[a-zA-Z0-9_\-]+$")
USER_PATTERN = re.compile(r"^[a-zA-Z0-9._\-]+$")

# -------------------------------------------------------------
# Allowlisted commands
# name -> (template, validation_regex)
# -------------------------------------------------------------

ALLOWED_COMMANDS = {

    # -----------------------------
    # Network
    # -----------------------------
    "ping": (
        "ping -c 4 {target}",
        HOST_PATTERN,
    ),

    "traceroute": (
        "traceroute {target}",
        HOST_PATTERN,
    ),

    "ipconfig": (
        "ip addr show",
        None,
    ),

    # -----------------------------
    # Disk / Hardware
    # -----------------------------
    "disk_usage": (
        "df -h",
        None,
    ),

    "memory_usage": (
        "free -m",
        None,
    ),

    "cpu_usage": (
        "top -n 1",
        None,
    ),

    # -----------------------------
    # Services
    # -----------------------------
    "service_status": (
        "systemctl status {service}",
        SERVICE_PATTERN,
    ),

    "journal": (
        "journalctl -u {service}",
        SERVICE_PATTERN,
    ),

    # -----------------------------
    # Docker
    # -----------------------------
    "docker_ps": (
        "docker ps",
        None,
    ),

    "docker_logs": (
        "docker logs {target}",
        HOST_PATTERN,
    ),

    # -----------------------------
    # Authentication / Security
    # -----------------------------
    "failed_logins": (
        "grep 'Failed password' /var/log/auth.log",
        None,
    ),

    "ssh_logs": (
        "journalctl -u ssh",
        None,
    ),

    "faillock": (
        "faillock --user {target}",
        USER_PATTERN,
    ),

    # -----------------------------
    # Database
    # -----------------------------
    "mysql_ping": (
        "mysqladmin ping",
        None,
    ),

    # -----------------------------
    # Mail
    # -----------------------------
    "mail_queue": (
        "mailq",
        None,
    ),
}


# -------------------------------------------------------------
# Exception
# -------------------------------------------------------------

class CommandNotAllowedError(Exception):
    pass


# -------------------------------------------------------------
# Safe builder
# -------------------------------------------------------------

def build_command(name: str, target: str | None = None) -> str:

    if name not in ALLOWED_COMMANDS:
        raise CommandNotAllowedError(
            f"'{name}' is not allowlisted."
        )

    template, pattern = ALLOWED_COMMANDS[name]

    if pattern is None:
        return template

    if target is None:
        raise CommandNotAllowedError(
            f"Command '{name}' requires a target."
        )

    if not pattern.fullmatch(target):
        raise CommandNotAllowedError(
            f"Target '{target}' failed validation."
        )

    return template.format(
        target=target,
        service=target,
    )
