FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    fonts-dejavu fonts-liberation \
    libfreetype6 libjpeg62-turbo \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . .

# Create directories
RUN mkdir -p /app/templates /app/assets /app/logs /tmp

EXPOSE $PORT

CMD ["python", "keepalive.py"]
