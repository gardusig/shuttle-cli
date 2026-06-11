FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

RUN apt-get update \
    && apt-get install -y --no-install-recommends bash git ca-certificates tar \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /workspace

CMD ["bash"]
