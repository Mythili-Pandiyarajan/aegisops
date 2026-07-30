"""
Production-ready log parser for AegisOps.

Features
--------
✓ Supports uploaded log files
✓ Falls back to sample logs (optional)
✓ Weighted relevance scoring
✓ Incident keyword matching
✓ Category keyword matching
✓ Severity scoring
✓ Multi-log support
✓ No hallucinations when no evidence exists
"""

from pathlib import Path
from collections import defaultdict
import re

##############################################################
# Demo sample logs
##############################################################

LOG_DIR = Path(__file__).resolve().parent.parent / "data" / "sample_logs"

DEFAULT_LOGS = [
    "server.log",
    "docker.log",
    "nginx_sample.log",
    "mail_relay.log",
]

##############################################################
# Keyword dictionaries
##############################################################

CATEGORY_KEYWORDS = {

    "security":[
        "login",
        "authentication",
        "auth",
        "password",
        "failed",
        "ssh",
        "sshd",
        "credential",
        "unauthorized",
        "vpn",
        "radius",
    ],

    "database":[
        "mysql",
        "postgres",
        "query",
        "connection",
        "timeout",
        "deadlock",
        "sql",
        "504",
    ],

    "application":[
        "nginx",
        "http",
        "api",
        "500",
        "502",
        "503",
        "upstream",
        "tomcat",
    ],

    "hardware":[
        "memory",
        "cpu",
        "disk",
        "oom",
        "thermal",
        "filesystem",
    ],

    "network":[
        "packet",
        "latency",
        "dns",
        "gateway",
        "vpn",
        "icmp",
        "firewall",
        "switch",
    ],

    "email":[
        "smtp",
        "relay",
        "mail",
        "postfix",
        "spamhaus",
        "bounce",
    ]
}

##############################################################
# Severity markers
##############################################################

SEVERITY = [

    "critical",

    "fatal",

    "panic",

    "error",

    "failed",

    "timeout",

    "timed out",

    "refused",

    "unreachable",

    "oom",

    "oomkilled",

    "blocked",

    "denied",

]

##############################################################


def _load_lines(log_path):

    if not Path(log_path).exists():

        return []

    with open(log_path,"r",errors="ignore") as f:

        return [x.strip() for x in f.readlines()]


##############################################################


def _score_line(line,incident_keywords,category_keywords):

    score=0

    lower=line.lower()

    keyword_hits=0

    for k in incident_keywords:

        if k in lower:

            score+=4

            keyword_hits+=1

    for k in category_keywords:

        if k in lower:

            score+=2

            keyword_hits+=1

    for sev in SEVERITY:

        if sev in lower:

            score+=3

    return score,keyword_hits


##############################################################


def search_logs(
        incident_text,
        category=None,
        uploaded_log_path=None,
        max_lines=10,
):

    incident_keywords=set(

        re.findall(

            r"[A-Za-z0-9]{3,}",

            incident_text.lower()

        )

    )

    category_keywords=set(

        CATEGORY_KEYWORDS.get(category,[])

    )

    ##########################################################

    files=[]

    if uploaded_log_path:

        files=[Path(uploaded_log_path)]

    else:

        files=[LOG_DIR/x for x in DEFAULT_LOGS]

    ##########################################################

    candidates=[]

    per_source=defaultdict(int)

    for file in files:

        for line in _load_lines(file):

            score,hits=_score_line(

                line,

                incident_keywords,

                category_keywords,

            )

            if hits==0:

                continue

            candidates.append(

                (

                    score,

                    file.name,

                    line,

                )

            )

    ##########################################################

    if len(candidates)==0:

        return []

    ##########################################################

    candidates.sort(

        key=lambda x:x[0],

        reverse=True,

    )

    results=[]

    for score,source,line in candidates:

        if per_source[source]>=4:

            continue

        results.append(

            (

                source,

                line,

            )

        )

        per_source[source]+=1

        if len(results)>=max_lines:

            break

    return results
