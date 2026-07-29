"""
Executes an already-built, already-validated command string inside the
aegisops sandbox container (built from sandbox/Dockerfile).

IMPORTANT ENVIRONMENT NOTE:
Docker containers generally cannot run inside Colab (no privileged Docker
daemon access there). This module detects that case and returns a clear
explanatory message rather than crashing -- so the rest of the pipeline
still runs end-to-end during Colab testing. For a real demo/deployment,
run this on a machine with Docker available (a local machine, or a cloud
VM), where actual command execution will work as designed.
"""

import subprocess

SANDBOX_CONTAINER_NAME = "aegisops-sandbox"


def _docker_available() -> bool:
    try:
        result = subprocess.run(
            ["docker", "info"], capture_output=True, timeout=5
        )
        return result.returncode == 0
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return False


def _container_running(name: str) -> bool:
    try:
        result = subprocess.run(
            ["docker", "ps", "--filter", f"name={name}", "--format", "{{.Names}}"],
            capture_output=True, text=True, timeout=5,
        )
        return name in result.stdout
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return False


def run_in_sandbox(command_str: str, timeout_seconds: int = 10) -> str:
    """
    Runs command_str inside the sandbox container via `docker exec`.

    Returns the command's stdout (or a clear explanatory message if
    Docker/the container isn't available in the current environment --
    this is expected and normal when testing in Colab).
    """
    if not _docker_available():
        return (
            "[sandbox unavailable: Docker is not accessible in this environment "
            "(expected in Colab). Run this on a machine with Docker to see real "
            f"output for: {command_str}]"
        )

    if not _container_running(SANDBOX_CONTAINER_NAME):
        return (
            f"[sandbox container '{SANDBOX_CONTAINER_NAME}' is not running. "
            f"Build and start it first: docker build -t aegisops-sandbox ./sandbox "
            f"&& docker run -d --name {SANDBOX_CONTAINER_NAME} aegisops-sandbox]"
        )

    try:
        result = subprocess.run(
            ["docker", "exec", SANDBOX_CONTAINER_NAME, "sh", "-c", command_str],
            capture_output=True, text=True, timeout=timeout_seconds,
        )
        output = result.stdout.strip()
        if result.returncode != 0:
            output += f"\n[exit code {result.returncode}] {result.stderr.strip()}"
        return output or "[command produced no output]"
    except subprocess.TimeoutExpired:
        return f"[command timed out after {timeout_seconds}s]"
