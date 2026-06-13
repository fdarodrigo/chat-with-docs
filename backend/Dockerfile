# ---- Builder stage: install Python dependencies into a venv-like prefix ----
FROM python:3.11-slim AS builder

WORKDIR /app

# Build tools required to compile any wheels without prebuilt binaries (e.g. for PyMuPDF).
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# ---- Runtime stage: slim image with only what's needed to run the app ----
FROM python:3.11-slim

WORKDIR /app

# Shared libraries required at runtime by PyMuPDF (MuPDF rendering backend).
RUN apt-get update && apt-get install -y --no-install-recommends \
    libglib2.0-0 \
    libgl1 \
    && rm -rf /var/lib/apt/lists/*

COPY --from=builder /root/.local /root/.local
COPY app ./app

ENV PATH=/root/.local/bin:$PATH \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
