# AURA production image — minimal, non-root
FROM python:3.12-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    AURA_ENVIRONMENT=production

WORKDIR /app

COPY pyproject.toml README.md ./
COPY src ./src

RUN pip install --no-cache-dir --upgrade pip \
 && pip install --no-cache-dir . \
 && addgroup --system aura && adduser --system --ingroup aura aura \
 && mkdir -p /data /app/data \
 && chown -R aura:aura /data /app/data \
 && rm -rf /root/.cache

USER aura

EXPOSE 8765

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
  CMD ["python", "-c", "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8765/health', timeout=3)"]

# Default: run the API server on 0.0.0.0 (K8s/Compose override with CMD)
ENTRYPOINT ["python", "-m", "aura.api.server"]
CMD ["0.0.0.0"]