# Isolated sandbox for the Shell Agent's allowlisted diagnostic commands.
# No host filesystem mounts, no network beyond what's needed for the
# demo. This container should never need write access to anything
# outside itself.

FROM debian:bookworm-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
    iputils-ping \
    iproute2 \
    procps \
    docker.io \
    && rm -rf /var/lib/apt/lists/*

# Run as a non-root user — the sandbox should not have privileges it
# doesn't need, even for read-only diagnostic commands.
RUN useradd -m sandboxuser
USER sandboxuser

CMD ["sleep", "infinity"]
