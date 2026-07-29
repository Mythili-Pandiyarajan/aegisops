from agents.shell_agent import _choose_command
name, target = _choose_command("VPN concentrator reached session limit 500/500")
print("command_name:", name)
print("target:", target)
