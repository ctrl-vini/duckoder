# The Duckoder web server. The language model runs in its own container, the ollama service in
# compose.yaml, or in Ollama installed on the host.
FROM python:3.14-slim

# Logs reach `docker logs` as soon as they are written, and no .pyc files end up in the image.
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

# The dependencies come first, so a change to the code does not install them again.
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY server.py .
COPY app ./app
COPY data/boards ./data/boards
COPY scripts ./scripts
COPY static ./static

# The server runs as an unprivileged user, who can read the code whatever the permissions in the
# checkout, and owns the folder the conversations are saved in; a new volume mounted there takes
# that owner.
RUN useradd --create-home --uid 1000 duckoder \
    && chmod -R a+rX /app \
    && mkdir data/conversations \
    && chown duckoder data/conversations
USER duckoder

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD ["python", "-c", "import os, urllib.request as r; r.urlopen('http://127.0.0.1:%s/version' % os.getenv('APP_PORT', '8000'), timeout=4)"]

CMD ["python", "server.py"]
