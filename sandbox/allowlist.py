"""
The command allowlist for the Shell Agent.

DESIGN RULE (do not weaken this):
The LLM never constructs a shell command string. It may only SELECT one
of the commands below by name, and supply a value for the declared
parameter (validated against the given pattern). This makes arbitrary
command injection structurally impossible rather than something we
merely try to detect.

All commands here are read-only / diagnostic. None of them mutate
system or application state.
"""

import re

# name -> (command template, parameter validation regex or None)
ALLOWED_COMMANDS = {
    "ping": ("ping -c 4 {target}", re.compile(r"^[a-zA-Z0-9.\-]+$")),
    "ipconfig": ("ip addr show", None),          # no parameters
    "disk_usage": ("df -h", None),
    "service_status": ("systemctl status {service}", re.compile(r"^[a-zA-Z0-9_\-]+$")),
    "docker_ps": ("docker ps", None),
}


class CommandNotAllowedError(Exception):
    pass


def build_command(name: str, target: str | None = None) -> str:
    """
    The only way to get a runnable command string. Raises if `name`
    isn't in the allowlist or if `target` fails validation for
    commands that take a parameter.
    """
    if name not in ALLOWED_COMMANDS:
        raise CommandNotAllowedError(f"'{name}' is not an allowlisted command")

    template, pattern = ALLOWED_COMMANDS[name]

    if pattern is None:
        return template

    if target is None or not pattern.match(target):
        raise CommandNotAllowedError(
            f"target '{target}' failed validation for command '{name}'"
        )

    return template.format(target=target, service=target)
