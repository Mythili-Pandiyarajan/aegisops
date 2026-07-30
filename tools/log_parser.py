"""
Production-ready log parser for AegisOps.

Features
--------
✓ Uploaded log support
✓ Category-aware filtering
✓ Weighted relevance scoring
✓ Prevents unrelated log selection
✓ Multi-log support
✓ No hallucinated evidence
"""

from pathlib import Path
from collections import defaultdict
import re


##############################################################
# Log directory
##############################################################

LOG_DIR = (
    Path(__file__).resolve().parent.parent
    / "data"
    / "sample_logs"
)


DEFAULT_LOGS = [
    "server.log",
    "docker.log",
    "nginx_sample.log",
    "mail_relay.log",
]


##############################################################
# Category keywords
##############################################################

CATEGORY_KEYWORDS = {

    "security": [
        "login",
        "authentication",
        "auth",
        "password",
        "failed password",
        "invalid user",
        "ssh",
        "sshd",
        "credential",
        "unauthorized",
        "account",
        "brute",
        "vpn",
        "radius",
    ],


    "database": [
        "mysql",
        "postgres",
        "sql",
        "deadlock",
        "query",
        "database",
        "connection pool",
    ],


    "application": [
        "nginx",
        "http",
        "api",
        "500",
        "502",
        "503",
        "upstream",
        "tomcat",
        "application",
    ],


    "hardware": [
        "memory",
        "cpu",
        "disk",
        "filesystem",
        "oom",
        "storage",
    ],


    "network": [
        "packet",
        "latency",
        "dns",
        "gateway",
        "firewall",
        "icmp",
        "vpn",
    ],


    "email": [
        "smtp",
        "relay",
        "postfix",
        "mail",
        "spamhaus",
        "bounce",
    ],
}



##############################################################
# File priority by category
##############################################################

CATEGORY_LOG_PRIORITY = {

    "security": [
        "server.log",
        "auth.log",
        "secure.log",
    ],


    "application": [
        "nginx_sample.log",
        "server.log",
    ],


    "database": [
        "server.log",
    ],


    "hardware": [
        "server.log",
        "docker.log",
    ],


    "network": [
        "server.log",
    ],


    "email": [
        "mail_relay.log",
    ],
}



##############################################################
# Severity words
##############################################################

SEVERITY = [

    "critical",
    "fatal",
    "panic",
    "error",
    "failed",
    "timeout",
    "refused",
    "denied",
    "blocked",
    "unreachable",

]



##############################################################
# Load logs
##############################################################

def _load_lines(path):

    if not Path(path).exists():

        return []

    with open(
        path,
        "r",
        errors="ignore"
    ) as f:

        return [
            line.strip()
            for line in f.readlines()
        ]



##############################################################
# Score log line
##############################################################

def _score_line(
        line,
        incident_keywords,
        category_keywords
):

    score = 0

    lower = line.lower()


    for word in incident_keywords:

        if word in lower:

            score += 3



    for word in category_keywords:

        if word in lower:

            score += 5



    for sev in SEVERITY:

        if sev in lower:

            score += 1


    return score



##############################################################
# Search logs
##############################################################

def search_logs(
        incident_text,
        category=None,
        uploaded_log_path=None,
        max_lines=10,
):


    incident_keywords = set(

        re.findall(
            r"[a-zA-Z0-9]{3,}",
            incident_text.lower()
        )

    )


    category_keywords = set(

        CATEGORY_KEYWORDS.get(
            category,
            []
        )

    )



    ##########################################################
    # Select files
    ##########################################################

    if uploaded_log_path:

        files = [
            Path(uploaded_log_path)
        ]

    else:

        files = []


        # category priority first

        priority_logs = CATEGORY_LOG_PRIORITY.get(
            category,
            DEFAULT_LOGS
        )


        for log in priority_logs:

            files.append(
                LOG_DIR / log
            )



    ##########################################################
    # Collect candidates
    ##########################################################

    candidates = []


    for file in files:


        for line in _load_lines(file):


            score = _score_line(

                line,

                incident_keywords,

                category_keywords,

            )


            if score > 0:

                candidates.append(

                    (
                        score,
                        file.name,
                        line
                    )

                )



    ##########################################################
    # No evidence
    ##########################################################

    if not candidates:

        return []



    ##########################################################
    # Rank
    ##########################################################

    candidates.sort(
        key=lambda x:x[0],
        reverse=True
    )



    results=[]

    source_count=defaultdict(int)



    for score,source,line in candidates:


        if source_count[source] >= 5:

            continue


        results.append(

            (
                source,
                line
            )

        )


        source_count[source]+=1



        if len(results)>=max_lines:

            break



    return results
