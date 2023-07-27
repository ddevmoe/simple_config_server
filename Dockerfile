FROM python:3.11.4-slim-bookworm

# Setup and run as a non-root user due to security concerns
RUN adduser --system --no-create-home nonroot

WORKDIR /app

COPY ./requirements.txt .

RUN python -m pip install -r requirements.txt --no-cache-dir

COPY . .

USER nonroot

CMD ["python", "app.py"]
