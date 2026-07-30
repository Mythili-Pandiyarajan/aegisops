# ============================================================
# AegisOps Shell Agent Diagnostic Sandbox
#
# Purpose:
# - Executes ONLY allowlisted read-only diagnostics
# - No host filesystem access
# - No privileged permissions
# - No shell command generation
# ============================================================


FROM debian:bookworm-slim


# ------------------------------------------------------------
# Install only required diagnostic utilities
# ------------------------------------------------------------

RUN apt-get update && apt-get install -y --no-install-recommends \
    iputils-ping \
    iproute2 \
    procps \
    grep \
    systemd \
    systemd-sysv \
    default-mysql-client \
    && rm -rf /var/lib/apt/lists/*



# ------------------------------------------------------------
# Create isolated non-root user
# ------------------------------------------------------------

RUN useradd \
    --create-home \
    --shell /bin/bash \
    sandboxuser


USER sandboxuser


WORKDIR /home/sandboxuser



# ------------------------------------------------------------
# Environment
# ------------------------------------------------------------

ENV HOME=/home/sandboxuser



# ------------------------------------------------------------
# Keep sandbox alive
# ------------------------------------------------------------

CMD ["sleep", "infinity"]
