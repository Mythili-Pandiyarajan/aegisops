"""
Lightweight log search tool for the Log Analysis Agent.

Deliberately simple line-based matching rather than a full log-parsing
framework -- for a portfolio-scale project, a transparent keyword/severity
match that you can explain line-by-line in an interview is more defensible
than an opaque "smart" parser you can't fully account for.

DESIGN NOTES (learned from testing):
1. Incident-text keywords are weighted higher than category keywords.
   The predicted_category comes from an LLM classifier that can be
   wrong -- trusting it equally can let a misclassification's keywords
   drown out log lines that are actually relevant to the real incident.
2. A MIN_RELEVANCE_SCORE floor exists so that when NOTHING genuinely
   relevant is found (e.g. no log file covers this incident type), the
   agent reports that honestly instead of confidently reasoning from
   whatever severity-marked lines happen to exist elsewhere. A line that
   only scores from a bare severity marker, with zero keyword overlap to
   the actual incident, is noise, not evidence.
"""

import re
from collections import defaultdict
from pathlib import Path

LOG_DIR = Path(__file__).resolve().parent.parent / "data" / "sample_logs"
LOG_FILES = ["server.log", "nginx_sample.log", "docker.log", "mail_relay.log"]

SEVERITY_MARKERS = re.compile(
    r"\b(ERROR|CRITICAL|OOMKilled|Out of memory|timed out|rejecting|failed|"
    r"deferred|blocked|refused)\b",
    re.IGNORECASE,
)

CATEGORY_KEYWORDS = {
    "network": ["vpn", "session", "concentrator", "link status", "radius"],
    "hardware": ["memory", "oom", "disk", "cpu", "thermal"],
    "database": ["upstream", "timed out", "connection pool", "query", "504"],
    "security": ["auth", "login", "failed", "unauthorized", "sshd"],
    "email": ["mail", "smtp", "relay", "bounce", "blocklist", "postfix", "spamhaus", "deferred"],
}

INCIDENT_KEYWORD_WEIGHT = 2
CATEGORY_KEYWORD_WEIGHT = 1
SEVERITY_WEIGHT = 2

MAX_LINES_PER_SOURCE = 4

# a line must have at least one real keyword hit (not just a bare
# severity marker) to count as genuine evidence, not noise.
MIN_KEYWORD_HITS = 1


def _read_all_lines() -> list:
    lines = []
    for filename in LOG_FILES:
        path = LOG_DIR / filename
        if not path.exists():
            continue
        with open(path) as f:
            for line in f:
                lines.append((filename, line.rstrip("\n")))
    return lines


def search_logs(incident_text: str, category: str = None, max_lines: int = 12) -> list:
    """
    Returns up to max_lines log lines relevant to the incident, as a list
    of (source_file, line) tuples, most-relevant first, diversified across
    log sources. Returns an empty list if nothing has genuine keyword
    relevance (severity markers alone don't count) -- callers should treat
    an empty result as "no relevant log evidence available", not retry
    with a looser search.
    """
    category_keywords = set(k.lower() for k in CATEGORY_KEYWORDS.get(category, []))
    incident_keywords = set(w.lower() for w in re.findall(r"[a-zA-Z0-9]{3,}", incident_text))

    scored = []
    for filename, line in _read_all_lines():
        lower = line.lower()
        keyword_hits = (
            sum(1 for kw in incident_keywords if kw in lower)
            + sum(1 for kw in category_keywords if kw in lower)
        )
        if keyword_hits < MIN_KEYWORD_HITS:
            continue  # severity marker alone isn't enough -- skip pure noise

        score = 0
        if SEVERITY_MARKERS.search(line):
            score += SEVERITY_WEIGHT
        score += INCIDENT_KEYWORD_WEIGHT * sum(1 for kw in incident_keywords if kw in lower)
        score += CATEGORY_KEYWORD_WEIGHT * sum(1 for kw in category_keywords if kw in lower)
        scored.append((score, filename, line))

    scored.sort(key=lambda x: x[0], reverse=True)

    results = []
    per_source_count = defaultdict(int)
    for score, filename, line in scored:
        if per_source_count[filename] >= MAX_LINES_PER_SOURCE:
            continue
        results.append((filename, line))
        per_source_count[filename] += 1
        if len(results) >= max_lines:
            break

    return results
