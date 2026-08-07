FROM python:3.11-slim

WORKDIR /app

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code (build context = raiz do repo)
COPY . .

# Create output directories
RUN mkdir -p outputs

EXPOSE 8080

# Entrypoint: uvicorn na $PORT do Railway + proxy TCP na 8080 (edge publico)
# escuta as DUAS portas — healthcheck interno (Railway sonda $PORT) e dominio
# publico (Target Port 8080) — sem 502/CORS falso no navegador.
CMD ["python", "entrypoint.py"]
