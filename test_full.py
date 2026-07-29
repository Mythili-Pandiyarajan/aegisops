from graph.build_graph import build_graph
app = build_graph()
result = app.invoke({"incident_text": "Users cannot connect to VPN", "incident_id": "INC001"})
print("log_findings:")
print(result.get("log_findings"))
print()
print("suspected_root_cause:")
print(result.get("suspected_root_cause"))
