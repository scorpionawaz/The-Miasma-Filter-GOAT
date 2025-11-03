FROM python:3.10-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*
ENV PYTHONUNBUFFERED=1 \
     GOOGLE_GENAI_USE_VERTEXAI=FALSE

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY ./app ./app

EXPOSE 8000

CMD ["adk", "api_server", "--host", "0.0.0.0", "--port", "8000", "."]