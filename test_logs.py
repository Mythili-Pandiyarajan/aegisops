from tools.log_parser import search_logs
for source, line in search_logs("Users cannot connect to VPN", category="network"):
    print(source, "-", line)
