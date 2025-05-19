# Usamos una imagen oficial de Python
FROM python:3.12-slim

# Variables de entorno para que Python no genere archivos .pyc y se comporte correctamente
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Establecemos el directorio de trabajo
WORKDIR /app

# Instalamos dependencias del sistema necesarias
RUN apt-get update && apt-get install -y \
    libpq-dev gcc && \
    apt-get clean

# Copiamos los archivos del proyecto al contenedor
COPY . /app/

# Instalamos las dependencias de Python
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

# Comando por defecto (puedes cambiarlo en docker-compose)
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]