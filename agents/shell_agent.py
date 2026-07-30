"""
AegisOps Shell Agent

The Shell Agent NEVER generates shell commands directly.
It selects an allowlisted command and lets build_command()
construct the final validated command.

Workflow:

Incident
    ↓
Root Cause
    ↓
Rule Engine
    ↓
(command_name, target)
    ↓
build_command()
    ↓
Validated Command
    ↓
Human Approval
"""

from sandbox.allowlist import (
    build_command,
    CommandNotAllowedError,
)

###############################################################
# Category defaults
###############################################################

CATEGORY_COMMANDS = {

    "security": ("failed_logins", None),

    "application": ("service_status", "nginx"),

    "database": ("mysql_ping", None),

    "hardware": ("disk_usage", None),

    "network": ("ping", "localhost"),

    "email": ("mail_queue", None),

    "docker": ("docker_ps", None),
}

###############################################################
# Root cause keyword mapping
###############################################################

KEYWORD_COMMANDS = {

    # ---------- Web ----------
    "nginx": ("service_status", "nginx"),

    "apache": ("service_status", "apache2"),

    # ---------- Database ----------
    "mysql": ("service_status", "mysql"),

    "postgres": ("service_status", "postgresql"),

    "database": ("mysql_ping", None),

    # ---------- Docker ----------
    "docker": ("docker_ps", None),

    "container": ("docker_ps", None),

    # ---------- Hardware ----------
    "disk": ("disk_usage", None),

    "filesystem": ("disk_usage", None),

    "storage": ("disk_usage", None),

    "memory": ("memory_usage", None),

    "oom": ("memory_usage", None),

    "cpu": ("cpu_usage", None),

    # ---------- Authentication ----------
    "failed password": ("failed_logins", None),

    "authentication": ("ssh_logs", None),

    "credential": ("failed_logins", None),

    "login": ("failed_logins", None),

    "ssh": ("ssh_logs", None),

    "vpn": ("ssh_logs", None),

    "account locked": ("faillock", "admin"),

    # ---------- Network ----------
    "dns": ("ping", "8.8.8.8"),

    "latency": ("ping", "8.8.8.8"),

    "packet": ("ping", "8.8.8.8"),

    "timeout": ("ping", "8.8.8.8"),

    "gateway": ("ping", "8.8.8.8"),

    # ---------- Email ----------
    "smtp": ("mail_queue", None),

    "relay": ("mail_queue", None),

    "mail": ("mail_queue", None),
}

###############################################################

def choose_command(category, root_cause):

    root = (root_cause or "").lower()

    # Keyword match first
    for keyword, value in KEYWORD_COMMANDS.items():

        if keyword in root:
            return value

    # Category fallback
    return CATEGORY_COMMANDS.get(category, (None, None))


###############################################################

def run_shell_agent(state):

    category = state.get("predicted_category")

    root = state.get("suspected_root_cause", "")

    command_name, target = choose_command(category, root)

    ###########################################################

    if command_name is None:

        return {

            "command_name": None,

            "target": None,

            "proposed_command": None,

            "approval_required": False,

            "command_status":
                "No suitable diagnostic command found."

        }

    ###########################################################

    try:

        command = build_command(
            command_name,
            target,
        )

    except CommandNotAllowedError as e:

        return {

            "command_name": command_name,

            "target": target,

            "proposed_command": None,

            "approval_required": False,

            "command_status": str(e),

        }

    ###########################################################

    return {

        "command_name": command_name,

        "target": target,

        "proposed_command": command,

        "approval_required": True,

        "command_status":
            "Awaiting human approval before execution.",

    }
