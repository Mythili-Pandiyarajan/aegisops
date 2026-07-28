from graph.build_graph import build_graph
app = build_graph()
result = app.invoke({"incident_text": "Users cannot connect to VPN", "incident_id": "INC001"})
print("retrieved_docs:", result.get("retrieved_docs"))
print("rag_summary:", result.get("rag_summary"))
