FROM python:3.11-slim-bookworm

WORKDIR /app

# OpenCV system dependencies (Debian Bookworm compatible)
RUN apt-get update && apt-get install -y --no-install-recommends \
    libglib2.0-0 \
    libgl1 \
    libgl1-mesa-glx \
    libgomp1 \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN useradd -m -u 1001 mluser && chown -R mluser:mluser /app
USER mluser

EXPOSE 8001

CMD ["uvicorn", "server:app", "--host", "0.0.0.0", "--port", "8001", "--workers", "1"]
