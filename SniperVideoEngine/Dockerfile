FROM python:3.11-slim

WORKDIR /app

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code (build context = SniperVideoEngine/ no Railway)
COPY . .

# Create output directories
RUN mkdir -p outputs

EXPOSE 8000

# Usa $PORT do Railway (fallback para 8000 local)
CMD uvicorn server:app --host 0.0.0.0 --port ${PORT:-8000} --proxy-headers
