"""
AegisOps Shell Agent

Selects a safe allowlisted diagnostic command based on the
incident category and suspected root cause.
"""

print(">>> SHELL AGENT FILE LOADED <<<")
print(__file__)

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

    "network": ("ping", "8.8.8.8"),

    "email": ("mail_queue", None),

    "docker": ("docker_ps", None),

}

###############################################################
# Keyword mapping
###############################################################

KEYWORD_COMMANDS = {

    # Security
    "failed password": ("failed_logins", None),
    "failed login": ("failed_logins", None),
    "authentication": ("failed_logins", None),
    "login": ("failed_logins", None),
    "ssh": ("ssh_logs", None),
    "brute": ("failed_logins", None),
    "brute force": ("failed_logins", None),
    "credential": ("failed_logins", None),
    "compromise": ("failed_logins", None),
    "account": ("failed_logins", None),

    # Application
    "nginx": ("service_status", "nginx"),
    "apache": ("service_status", "apache2"),

    # Database
    "mysql": ("mysql_ping", None),
    "postgres": ("mysql_ping", None),
    "database": ("mysql_ping", None),

    # Hardware
    "disk": ("disk_usage", None),
    "filesystem": ("disk_usage", None),
    "storage": ("disk_usage", None),
    "memory": ("memory_usage", None),
    "oom": ("memory_usage", None),
    "cpu": ("cpu_usage", None),

    # Docker
    "docker": ("docker_ps", None),
    "container": ("docker_ps", None),

    # Mail
    "smtp": ("mail_queue", None),
    "mail": ("mail_queue", None),

    # Network
    "dns": ("ping", "8.8.8.8"),
    "latency": ("ping", "8.8.8.8"),
    "timeout": ("ping", "8.8.8.8"),

}

###############################################################
# Choose Command
###############################################################

def choose_command(category, text):

    text = str(text).lower()

    print("SEARCH TEXT:")
    print(text)

    for keyword, value in KEYWORD_COMMANDS.items():

        if keyword in text:

            print(f"MATCHED KEYWORD: {keyword}")

            return value

    print("NO KEYWORD MATCH")

    return CATEGORY_COMMANDS.get(
        category,
        (None, None),
    )


###############################################################
# Shell Agent
###############################################################

def run_shell_agent(state):

    print(">>> run_shell_agent() CALLED <<<")

    print("\n==============================")
    print("SHELL AGENT STARTED")
    print("==============================")

    category = state.get(
        "predicted_category",
        "",
    )

    root = state.get(
        "suspected_root_cause",
        "",
    )

    incident = state.get(
        "incident_text",
        "",
    )

    combined_text = f"{root} {incident}"

    print("CATEGORY :", category)
    print("ROOT :", root)
    print("INCIDENT :", incident)

    ###########################################################

    command_name, target = choose_command(
        category,
        combined_text,
    )

    print("COMMAND :", command_name)
    print("TARGET :", target)

    ###########################################################

    if command_name is None:

        print("NO COMMAND SELECTED")

        return {

            "command_name": None,

            "target": None,

            "proposed_command": None,

            "proposed_commands": [],

            "approval_required": False,

            "command_status":
                "No suitable diagnostic command found.",

        }

    ###########################################################

    try:

        command = build_command(
            command_name,
            target,
        )

        print("COMMAND BUILT:", command)

    except CommandNotAllowedError as e:

        print("ALLOWLIST ERROR:", e)

        return {

            "command_name": command_name,

            "target": target,

            "proposed_command": None,

            "proposed_commands": [],

            "approval_required": False,

            "command_status": str(e),

        }

    ###########################################################

    return {

        "command_name": command_name,

        "target": target,

        "proposed_command": command,

        "proposed_commands": [
            command
        ],

        "approval_required": True,

        "command_status":
            "Awaiting human approval before execution.",

    }
