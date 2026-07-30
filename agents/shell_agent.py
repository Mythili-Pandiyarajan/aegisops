"""
AegisOps Shell Agent

Responsibilities
----------------
✓ Never invent shell commands
✓ Uses only allowlisted commands
✓ Rule-based command selection
✓ Human approval required
✓ Read-only diagnostics only
"""

from sandbox.allowlist import ALLOWED_COMMANDS


###############################################################
# Category defaults
###############################################################

CATEGORY_COMMANDS = {

    "security": [
        "grep 'Failed password' /var/log/auth.log",
        "journalctl -u ssh",
        "faillock --user",
    ],

    "application": [
        "systemctl status nginx",
        "journalctl -u nginx",
    ],

    "database": [
        "systemctl status mysql",
        "mysqladmin ping",
    ],

    "docker": [
        "docker ps",
        "docker logs",
    ],

    "hardware": [
        "df -h",
        "free -m",
        "top -n 1",
    ],

    "network": [
        "ping",
        "traceroute",
    ],

    "email": [
        "systemctl status postfix",
        "mailq",
    ],
}


###############################################################
# Root-cause keywords
###############################################################

KEYWORD_COMMANDS = {

    "nginx": "systemctl status nginx",

    "mysql": "systemctl status mysql",

    "postgres": "systemctl status postgresql",

    "docker": "docker ps",

    "oom": "free -m",

    "memory": "free -m",

    "disk": "df -h",

    "filesystem": "df -h",

    "cpu": "top -n 1",

    "ssh": "journalctl -u ssh",

    "failed password": "grep 'Failed password' /var/log/auth.log",

    "authentication": "journalctl -u ssh",

    "credential": "grep 'Failed password' /var/log/auth.log",

    "vpn": "journalctl -u ssh",

    "dns": "ping",

    "latency": "ping",

    "timeout": "ping",

    "packet": "ping",

}


###############################################################

def choose_command(category, root_cause):

    root = (root_cause or "").lower()

    ###########################################################
    # Keyword match first
    ###########################################################

    for keyword, command in KEYWORD_COMMANDS.items():

        if keyword in root:

            return command

    ###########################################################
    # Category fallback
    ###########################################################

    commands = CATEGORY_COMMANDS.get(category)

    if commands:

        return commands[0]

    return None


###############################################################

def validate(command):

    if command is None:

        return False

    return command in ALLOWED_COMMANDS


###############################################################

def run_shell_agent(state):

    category = state.get("predicted_category")

    root = state.get("suspected_root_cause", "")

    command = choose_command(category, root)

    ###########################################################

    if not validate(command):

        return {

            "proposed_command": None,

            "approval_required": False,

            "command_status":
                "No safe diagnostic command available."

        }

    ###########################################################

    return {

        "proposed_command": command,

        "approval_required": True,

        "command_status":
            "Awaiting human approval before execution."

    }
