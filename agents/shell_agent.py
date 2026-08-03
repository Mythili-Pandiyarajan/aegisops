"""
AegisOps Shell Agent

Selects a safe allowlisted diagnostic command based on the
incident category and suspected root cause.

FIXED: choose_command() used to return on the FIRST keyword match found
in KEYWORD_COMMANDS' fixed dict order, searching the incident title, root
cause analysis, and log text all mashed into one blob. That meant a
generic symptom word in the incident TITLE (e.g. "login failures") could
win over the actual diagnosed root cause (e.g. "disk space issue") just
because "login" happens to be checked before "disk" in the dict -- even
when the log evidence and root-cause analysis both clearly point
elsewhere. Fixed by scoring ALL keyword matches instead of stopping at
the first one, and weighting root-cause text and log evidence higher
than the raw incident title, since the title is the user's own symptom
report and is the noisiest of the three signals.
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

# Root-cause analysis and log evidence are the analysis outputs the
# diagnostic step should respond to; the raw incident title/description
# is just the user's symptom report and is the noisiest of the three
# (it commonly restates generic words like "login" or "down" that don't
# reflect the actual technical cause once investigated).
ROOT_CAUSE_WEIGHT = 3
LOG_TEXT_WEIGHT = 2
INCIDENT_TEXT_WEIGHT = 1


###############################################################
# Choose Command
###############################################################

def choose_command(category, root_cause_text, incident_text, log_text):

    root_cause_text = str(root_cause_text).lower()
    incident_text = str(incident_text).lower()
    log_text = str(log_text).lower()

    print("ROOT CAUSE TEXT:", root_cause_text)
    print("INCIDENT TEXT:", incident_text)
    print("LOG TEXT:", log_text[:300])

    scores = {}
    for keyword, value in KEYWORD_COMMANDS.items():
        count = (
            root_cause_text.count(keyword) * ROOT_CAUSE_WEIGHT
            + log_text.count(keyword) * LOG_TEXT_WEIGHT
            + incident_text.count(keyword) * INCIDENT_TEXT_WEIGHT
        )
        if count:
            scores[value] = scores.get(value, 0) + count

    if scores:
        best_value = max(scores, key=scores.get)
        print("KEYWORD SCORES:", scores)
        print("CHOSEN:", best_value)
        return best_value

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

    uploaded_log_path = state.get(
        "uploaded_log_path"
    )

    log_text = ""

    if uploaded_log_path:
        try:
            with open(
                uploaded_log_path,
                "r",
                encoding="utf-8",
                errors="ignore",
            ) as f:
                log_text = f.read()

        except Exception as e:
            print("Could not read uploaded log:", e)

    print("CATEGORY :", category)
    print("ROOT :", root)
    print("INCIDENT :", incident)
    print("UPLOADED LOG PATH :", uploaded_log_path)


    ###########################################################
    # Select command
    ###########################################################

    command_name, target = choose_command(
        category,
        root,
        incident,
        log_text,
    )


    print("COMMAND :", command_name)
    print("TARGET :", target)



    ###########################################################
    # No command
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
    # Build allowlisted command
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
    # Successful command proposal
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
