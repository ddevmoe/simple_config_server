FROM python:3.11.4-slim-bookworm

LABEL org.opencontainers.image.source=https://github.com/ddevmoe/simple_config_server
LABEL org.opencontainers.image.description="Simple Config Server's Official Image"
LABEL org.opencontainers.image.licenses=MIT

# Setup and run as a non-root user due to security concerns
RUN adduser --system --no-create-home nonroot

WORKDIR /app

COPY ./requirements.txt .

RUN python -m pip install -r requirements.txt --no-cache-dir

COPY . .

USER nonroot

CMD ["python", "app.py"]
