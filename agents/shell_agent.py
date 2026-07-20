"""
Shell Agent — proposes ONE allowlisted diagnostic command based on the
suspected root cause, and only executes it inside the Docker sandbox
after human_approved is True.

The LLM's role here is narrow and deliberately limited: pick a command
NAME and a target parameter from the allowlist. It never sees or
produces a raw shell string — see sandbox/allowlist.py for why.
"""

from graph.state import AegisOpsState
from sandbox.allowlist import build_command, CommandNotAllowedError

# TODO: wire to actual Docker sandbox exec, e.g. via `docker exec`
# against a pre-built aegisops-sandbox container with no host mounts.


def run_shell_agent(state: AegisOpsState) -> dict:
    # TODO: LLM call to pick (command_name, target) from suspected_root_cause
    command_name = None
    target = None

    if command_name is None:
        return {"proposed_commands": [], "command_output": None}

    try:
        command_str = build_command(command_name, target)
    except CommandNotAllowedError as e:
        return {"proposed_commands": [], "command_output": f"blocked: {e}"}

    if not state.get("human_approved"):
        # Surface for approval in the Streamlit UI; do not execute yet.
        return {"proposed_commands": [command_str], "command_output": None}

    # TODO: execute command_str inside the sandbox container and capture output
    output = ""
    return {"proposed_commands": [command_str], "command_output": output}
