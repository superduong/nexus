FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends gcc && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000
# Render free: không có preDeployCommand — chạy migrate mỗi lần container khởi động (idempotent với revision hiện tại).
# Render và nhiều PaaS inject biến PORT — mặc định 8000 khi chạy local.
CMD ["sh", "-c", "alembic upgrade head && uvicorn api.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
