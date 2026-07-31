def run_shell_agent(state):

    category = state.get("predicted_category", "")

    root = state.get("suspected_root_cause", "")

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

            "command_status":
                "No suitable diagnostic command found.",

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

        "command_status":
            "Awaiting human approval before execution.",

    }
