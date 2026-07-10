FROM python:3.12-slim

WORKDIR /app

# Install build dependencies and clean up
RUN apt-get update && apt-get install -y --no-install-recommends gcc libssl-dev && rm -rf /var/lib/apt/lists/*

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY . /app

EXPOSE 8001

CMD ["gunicorn", "server:app", "-k", "uvicorn.workers.UvicornWorker", "--bind", "0.0.0.0:8001"]
