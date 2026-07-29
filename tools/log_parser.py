"""
Lightweight log search tool for the Log Analysis Agent.

Deliberately simple line-based matching rather than a full log-parsing
framework -- for a portfolio-scale project, a transparent keyword/severity
match that you can explain line-by-line in an interview is more defensible
than an opaque "smart" parser you can't fully account for.
"""

import re
from pathlib import Path

LOG_DIR = Path(__file__).resolve().parent.parent / "data" / "sample_logs"
LOG_FILES = ["server.log", "nginx_sample.log", "docker.log"]

# lines containing any of these are treated as "signal" (worth surfacing)
# even if they don't match a specific keyword -- catches genuine errors
# the keyword list might miss.
SEVERITY_MARKERS = re.compile(
    r"\b(ERROR|CRITICAL|OOMKilled|Out of memory|timed out|rejecting|failed)\b",
    re.IGNORECASE,
)

# Maps incident category -> extra keywords likely to appear in relevant log lines.
CATEGORY_KEYWORDS = {
    "network": ["vpn", "session", "concentrator", "link status", "radius"],
    "hardware": ["memory", "oom", "disk", "cpu", "thermal"],
    "database": ["upstream", "timed out", "connection pool", "query", "504"],
    "security": ["auth", "login", "failed", "unauthorized", "sshd"],
    "email": ["mail", "smtp", "relay", "bounce", "blocklist"],
}


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
    of (source_file, line) tuples, most-severe/most-keyword-matched first.
    """
    keywords = CATEGORY_KEYWORDS.get(category, [])
    # also pull simple keyword hints straight from the incident text itself
    incident_words = [w.lower() for w in re.findall(r"[a-zA-Z]{4,}", incident_text)]
    all_keywords = set(k.lower() for k in keywords) | set(incident_words)

    scored = []
    for filename, line in _read_all_lines():
        lower = line.lower()
        score = 0
        if SEVERITY_MARKERS.search(line):
            score += 2
        score += sum(1 for kw in all_keywords if kw in lower)
        if score > 0:
            scored.append((score, filename, line))

    scored.sort(key=lambda x: x[0], reverse=True)
    return [(filename, line) for _, filename, line in scored[:max_lines]]
