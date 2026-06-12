# shuttle-cli dev/test base image: Python 3.12, git, and editable install with dev deps.
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

ARG DOCKER_CLI_VERSION=27.3.1
RUN apt-get update \
    && apt-get install -y --no-install-recommends bash git ca-certificates tar curl \
    && case "$(uname -m)" in \
         x86_64) docker_arch=x86_64 ;; \
         aarch64) docker_arch=aarch64 ;; \
         *) echo "unsupported architecture: $(uname -m)" >&2; exit 1 ;; \
       esac \
    && curl -fsSL "https://download.docker.com/linux/static/stable/${docker_arch}/docker-${DOCKER_CLI_VERSION}.tgz" \
         | tar xz -C /usr/local/bin --strip-components=1 docker/docker \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /opt/shuttle-cli

# Dependency layer (rebuild when pyproject or package changes).
COPY pyproject.toml README.md ./
COPY shuttle ./shuttle
RUN pip install --no-cache-dir -e ".[dev]"

# Runtime tests copy a fresh tree to /tmp/shuttle-cli; this layer documents the onboard layout.
WORKDIR /workspace
CMD ["bash"]
