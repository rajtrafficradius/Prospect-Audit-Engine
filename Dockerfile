FROM python:3.11-slim

# Set working directory
WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Install system dependencies including Node.js 20.x
RUN apt-get update && apt-get install -y \
    curl \
    wget \
    gnupg \
    fontconfig \
    fonts-dejavu-core \
    fonts-liberation \
    fonts-noto-core \
    && curl -fsSL https://deb.nodesource.com/setup_20.x | bash - \
    && apt-get install -y nodejs \
    && fc-cache -f -v \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements & package.json
COPY requirements.txt .
COPY package*.json ./

# Install Python and Node dependencies
RUN pip install --no-cache-dir -r requirements.txt \
    && npm install

# Install Playwright browsers & system dependencies for Chromium
RUN npx playwright install chromium \
    && npx playwright install-deps chromium

# Copy the rest of the application
COPY . .

# Expose the app port (Railway will inject PORT at runtime)
EXPOSE 8000

# Start command
CMD uvicorn src.api:app --host 0.0.0.0 --port ${PORT:-8000}
