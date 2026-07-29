from agents.shell_agent import run_shell_agent

result = run_shell_agent({
    "suspected_root_cause": "VPN concentrator reached session limit 500/500",
    "human_approved": True
})
print(result)
