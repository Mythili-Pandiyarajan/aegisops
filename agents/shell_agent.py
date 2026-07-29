"""
Shell Agent — proposes ONE allowlisted diagnostic command based on the
suspected root cause, and only executes it inside the Docker sandbox
after human_approved is True.

The LLM's role here is narrow and deliberately limited: pick a command
NAME and a target parameter from the allowlist. It never sees or
produces a raw shell string -- see sandbox/allowlist.py for why. If the
LLM names anything outside ALLOWED_COMMANDS, build_command() rejects it
structurally; this agent never falls back to running whatever the LLM said.
"""

import os
import json
from groq import Groq

from graph.state import AegisOpsState
from sandbox.allowlist import build_command, CommandNotAllowedError, ALLOWED_COMMANDS
from tools.sandbox_executor import run_in_sandbox

_client = None


def _get_client():
    global _client
    if _client is None:
        api_key = os.environ.get("GROQ_API_KEY")
        if not api_key:
            raise RuntimeError("GROQ_API_KEY not set.")
        _client = Groq(api_key=api_key)
    return _client


def _choose_command(suspected_root_cause: str) -> tuple:
    """
    Asks the LLM to pick ONE command name (from ALLOWED_COMMANDS only)
    and an optional target, based on the suspected root cause.

    Returns (command_name, target) -- either can be None if the LLM
    decides no diagnostic command is warranted, or if its choice fails
    to parse/validate (fail closed, not open).
    """
    if not suspected_root_cause:
        return None, None

    command_names = list(ALLOWED_COMMANDS.keys())
    prompt = (
        f"Suspected root cause: {suspected_root_cause}\n\n"
        f"Choose exactly ONE diagnostic command from this list that would "
        f"help confirm the root cause: {command_names}\n\n"
        "Some commands take a target (a hostname for 'ping', a service name "
        "for 'service_status'); others take none. If no command from the "
        "list is relevant, respond with null for command_name.\n\n"
        "Respond with ONLY a JSON object, no other text:\n"
        '{"command_name": "<one of the list above, or null>", "target": "<string or null>"}'
    )

    client = _get_client()
    response = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.0,
        max_tokens=80,
    )

    raw = response.choices[0].message.content.strip()
    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError:
        cleaned = raw.strip("`").replace("json", "", 1).strip()
        try:
            parsed = json.loads(cleaned)
        except json.JSONDecodeError:
            return None, None  # fail closed: unparseable response proposes nothing

    command_name = parsed.get("command_name")
    target = parsed.get("target")

    if command_name not in ALLOWED_COMMANDS:
        return None, None

    return command_name, target


def run_shell_agent(state: AegisOpsState) -> dict:
    command_name, target = _choose_command(state.get("suspected_root_cause", ""))

    if command_name is None:
        return {"proposed_commands": [], "command_output": None}

    try:
        command_str = build_command(command_name, target)
    except CommandNotAllowedError as e:
        return {"proposed_commands": [], "command_output": f"blocked: {e}"}

    if not state.get("human_approved"):
        # Surface for approval in the Streamlit UI; do not execute yet.
        return {"proposed_commands": [command_str], "command_output": None}

    output = run_in_sandbox(command_str)
    return {"proposed_commands": [command_str], "command_output": output}
