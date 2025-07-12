# dockerfile based off https://docs.astral.sh/uv/guides/integration/docker/#installing-uv
FROM python:3.12-slim-bookworm

COPY --from=ghcr.io/astral-sh/uv:0.4.15 /uv /bin/uv

ADD . /app
WORKDIR /app
RUN uv sync --frozen

CMD  ["uv", "run", "slack-ai-agent-reference-file.py"]



