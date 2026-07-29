from graph.build_graph import build_graph
app = build_graph()
result = app.invoke({"incident_text": "Users cannot connect to VPN", "incident_id": "INC001"})
print(result["manager_summary"])
print("risk_level:", result["risk_level"])
