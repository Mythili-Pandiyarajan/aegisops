"""
AegisOps Sandbox Command Allowlist

Security Rules:
----------------
- LLM never creates shell commands.
- Shell Agent selects only command names.
- This module builds validated read-only commands.
- No destructive commands allowed.
"""

import re


# ============================================================
# Validation Patterns
# ============================================================

HOST_PATTERN = re.compile(
    r"^[a-zA-Z0-9.\-_]+$"
)

SERVICE_PATTERN = re.compile(
    r"^[a-zA-Z0-9_\-]+$"
)

USER_PATTERN = re.compile(
    r"^[a-zA-Z0-9._\-@]+$"
)

CONTAINER_PATTERN = re.compile(
    r"^[a-zA-Z0-9._\-]+$"
)


# ============================================================
# Allowed Commands
# ============================================================

ALLOWED_COMMANDS = {


    # -------------------------
    # Network Diagnostics
    # -------------------------

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



    # -------------------------
    # Hardware Diagnostics
    # -------------------------

    "disk_usage": (
        "df -h",
        None,
    ),


    "memory_usage": (
        "free -m",
        None,
    ),


    "cpu_usage": (
        "top -b -n 1",
        None,
    ),



    # -------------------------
    # Service Diagnostics
    # -------------------------

    "service_status": (
        "systemctl status {service}",
        SERVICE_PATTERN,
    ),


    "journal": (
        "journalctl -u {service} --no-pager",
        SERVICE_PATTERN,
    ),



    # -------------------------
    # Docker Diagnostics
    # -------------------------

    "docker_ps": (
        "docker ps",
        None,
    ),


    "docker_logs": (
        "docker logs {target}",
        CONTAINER_PATTERN,
    ),



    # -------------------------
    # Security Diagnostics
    # -------------------------

    "failed_logins": (
        "grep 'Failed password' /var/log/auth.log",
        None,
    ),


    "ssh_logs": (
        "journalctl -u sshd --no-pager",
        None,
    ),


    "faillock": (
        "faillock --user {target}",
        USER_PATTERN,
    ),



    # -------------------------
    # Database
    # -------------------------

    "mysql_ping": (
        "mysqladmin ping",
        None,
    ),



    # -------------------------
    # Email
    # -------------------------

    "mail_queue": (
        "mailq",
        None,
    ),

}



# ============================================================
# Exception
# ============================================================

class CommandNotAllowedError(Exception):
    pass



# ============================================================
# Secure Command Builder
# ============================================================

def build_command(
        name: str,
        target: str | None = None
) -> str:


    if name not in ALLOWED_COMMANDS:

        raise CommandNotAllowedError(
            f"Command '{name}' is not allowlisted."
        )


    template, validator = ALLOWED_COMMANDS[name]


    # Commands without parameters

    if validator is None:

        return template



    # Commands requiring parameters

    if target is None:

        raise CommandNotAllowedError(
            f"Command '{name}' requires a validated target."
        )


    if not validator.fullmatch(target):

        raise CommandNotAllowedError(
            f"Invalid target: {target}"
        )


    return template.format(
        target=target,
        service=target,
    )
