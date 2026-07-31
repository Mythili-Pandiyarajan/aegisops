"""
AegisOps Shell Agent
"""

from sandbox.allowlist import (
    build_command,
    CommandNotAllowedError,
)

##########################################################
# Default category mapping
##########################################################

CATEGORY_COMMANDS = {

    "security": ("failed_logins", None),

    "application": ("service_status", "nginx"),

    "database": ("mysql_ping", None),

    "hardware": ("disk_usage", None),

    "network": ("ping", "localhost"),

    "email": ("mail_queue", None),

    "docker": ("docker_ps", None),

}

##########################################################
# Keyword mapping
##########################################################

KEYWORD_COMMANDS = {

    "brute": ("failed_logins", None),

    "credential": ("failed_logins", None),

    "failed login": ("failed_logins", None),

    "failed ssh": ("failed_logins", None),

    "authentication": ("failed_logins", None),

    "ssh": ("ssh_logs", None),

    "vpn": ("ssh_logs", None),

    "mysql": ("mysql_ping", None),

    "postgres": ("mysql_ping", None),

    "disk": ("disk_usage", None),

    "filesystem": ("disk_usage", None),

    "memory": ("memory_usage", None),

    "oom": ("memory_usage", None),

    "cpu": ("cpu_usage", None),

    "docker": ("docker_ps", None),

    "container": ("docker_ps", None),

    "nginx": ("service_status", "nginx"),

    "apache": ("service_status", "apache2"),

    "smtp": ("mail_queue", None),

    "mail": ("mail_queue", None),

}

##########################################################
# Command selection
##########################################################

def choose_command(category, root_cause):

    root = str(root_cause).lower()

    print("ROOT CAUSE:", root)

    for keyword, command in KEYWORD_COMMANDS.items():

        if keyword in root:

            print("Matched:", keyword)

            return command

    print("Category fallback:", category)

    return CATEGORY_COMMANDS.get(category, (None, None))


##########################################################
# Agent
##########################################################

def run_shell_agent(state):

    category = state.get("predicted_category", "")

    root = (
    state.get("suspected_root_cause", "")
    + " "
    + state.get("incident_text", "")
)

    print("CATEGORY:", category)
    print("ROOT:", root)

    command_name, target = choose_command(
        category,
        root,
    )

    if command_name is None:

        return {

            "command_name": None,

            "target": None,

            "proposed_command": None,

            "proposed_commands": [],

            "approval_required": False,

            "command_status": "No suitable diagnostic command found.",

        }

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

            "proposed_commands": [],

            "approval_required": False,

            "command_status": str(e),

        }

    return {

        "command_name": command_name,

        "target": target,

        "proposed_command": command,

        "proposed_commands": [command],

        "approval_required": True,

        "command_status": "Awaiting human approval before execution.",

    }
