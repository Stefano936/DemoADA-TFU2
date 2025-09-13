FROM python:3.10-slim

WORKDIR /app

# Instalar dependencias
COPY requirements.txt .
RUN pip install -r requirements.txt

# Copiar aplicación
COPY . .

# Exponer puerto
EXPOSE 8081

# Comando para ejecutar la aplicación
CMD ["python", "app.py"]
