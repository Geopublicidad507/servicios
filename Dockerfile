FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    pkg-config \
    libfreetype6-dev \
    libpng-dev \
    python3-dev \
    build-essential \
    libffi-dev \
    libjpeg-dev \
    zlib1g-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create necessary directories
RUN mkdir -p uploads uploads/documents uploads/receipts uploads/maintenance uploads/profiles backups logs temp

# Expose port
EXPOSE 5003

# Copy startup script
COPY start.sh /usr/local/bin/
RUN chmod +x /usr/local/bin/start.sh

# Use startup script
CMD ["start.sh"]