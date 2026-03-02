FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Crear directorio de datos si no existe
RUN mkdir -p /data

EXPOSE 8080

CMD ["python", "start.py"]
