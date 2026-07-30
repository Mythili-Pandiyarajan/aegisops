"""
AegisOps Shell Agent

Responsibilities:
- Select safe diagnostic commands from allowlist
- Never generate arbitrary shell commands
- Return validated command proposal
- Require human approval before execution
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

    "nginx": ("service_status", "nginx"),

    "apache": ("service_status", "apache2"),


    "mysql": ("service_status", "mysql"),

    "postgres": ("service_status", "postgresql"),

    "database": ("mysql_ping", None),


    "docker": ("docker_ps", None),

    "container": ("docker_ps", None),


    "disk": ("disk_usage", None),

    "filesystem": ("disk_usage", None),

    "storage": ("disk_usage", None),

    "memory": ("memory_usage", None),

    "oom": ("memory_usage", None),


    "failed password": ("failed_logins", None),

    "authentication": ("failed_logins", None),

    "credential": ("failed_logins", None),

    "login": ("failed_logins", None),

    "ssh": ("ssh_logs", None),

    "vpn": ("ssh_logs", None),

    "account locked": ("faillock", "admin"),


    "dns": ("ping", "8.8.8.8"),

    "latency": ("ping", "8.8.8.8"),

    "timeout": ("ping", "8.8.8.8"),


    "smtp": ("mail_queue", None),

    "relay": ("mail_queue", None),

    "mail": ("mail_queue", None),
}


###############################################################
# Command selection
###############################################################

def choose_command(category, root_cause):

    root = str(root_cause).lower()

    for keyword, command in KEYWORD_COMMANDS.items():

        if keyword in root:
            return command


    return CATEGORY_COMMANDS.get(
        category,
        (None, None)
    )



###############################################################
# Shell Agent
###############################################################

def run_shell_agent(state):

    category = state.get(
        "predicted_category"
    )

    root = state.get(
        "suspected_root_cause",
        ""
    )


    command_name, target = choose_command(
        category,
        root
    )


    ###########################################################
    # No command
    ###########################################################

    if command_name is None:

        return {

            "command_name": None,

            "target": None,

            "proposed_command": None,

            "proposed_commands": [],

            "approval_required": False,

            "command_status":
                "No suitable diagnostic command found."
        }


    ###########################################################
    # Build allowlisted command
    ###########################################################

    try:

        command = build_command(
            command_name,
            target
        )


    except CommandNotAllowedError as e:

        return {

            "command_name": command_name,

            "target": target,

            "proposed_command": None,

            "proposed_commands": [],

            "approval_required": False,

            "command_status": str(e)

        }



    ###########################################################
    # Successful command proposal
    ###########################################################

    return {

        "command_name": command_name,

        "target": target,


        # Existing state compatibility
        "proposed_command": command,


        # App.py compatibility
        "proposed_commands": [
            command
        ],


        "approval_required": True,


        "command_status":
            "Awaiting human approval before execution."

    }
