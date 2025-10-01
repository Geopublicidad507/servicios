# Configuración Docker - PH Control

Este documento detalla la configuración de Docker para el sistema PH Control.

## Estructura de Contenedores

El sistema PH Control utiliza tres contenedores principales:

1. **ph-web**: Aplicación web Flask
2. **ph-database**: Base de datos PostgreSQL
3. **ph-redis**: Servidor Redis para caché y colas

## Configuración de Docker Compose

El archivo `docker-compose.yml` define la configuración de los contenedores:

```yaml
services:
  ph-web:
    build: .
    container_name: ph-control-web
    restart: unless-stopped
    ports:
      - "5003:5003"
    environment:
      - FLASK_ENV=development
      - DATABASE_URL=postgresql://phcontrol:phcontrol123@ph-database:5432/phcontrol_db
      - SECRET_KEY=dev-secret-key-change-in-production-ph-control-2024
      - PORT=5003
      - DEBUG=True
      # Configuración de inicialización
      - CREATE_SAMPLE_DATA=true
      - SKIP_INIT=false
    depends_on:
      - ph-database
    volumes:
      - .:/app
      - ph_uploads:/app/uploads
    networks:
      - ph-network

  ph-database:
    image: postgres:15
    container_name: ph-control-database
    restart: unless-stopped
    environment:
      - POSTGRES_DB=phcontrol_db
      - POSTGRES_USER=phcontrol
      - POSTGRES_PASSWORD=phcontrol123
    volumes:
      - ph_postgres_data:/var/lib/postgresql/data
      - ./init.sql:/docker-entrypoint-initdb.d/init.sql
    ports:
      - "5435:5432"
    networks:
      - ph-network

  ph-redis:
    image: redis:7-alpine
    container_name: ph-control-redis
    restart: unless-stopped
    ports:
      - "6380:6379"
    networks:
      - ph-network

volumes:
  ph_postgres_data:
  ph_uploads:

networks:
  ph-network:
    driver: bridge
```

## Variables de Entorno

### Contenedor ph-web

| Variable | Descripción | Valor por defecto |
|----------|-------------|-------------------|
| FLASK_ENV | Entorno de Flask | development |
| DATABASE_URL | URL de conexión a la base de datos | postgresql://phcontrol:phcontrol123@ph-database:5432/phcontrol_db |
| SECRET_KEY | Clave secreta para sesiones | dev-secret-key-change-in-production-ph-control-2024 |
| PORT | Puerto de la aplicación | 5003 |
| DEBUG | Modo debug | True |
| CREATE_SAMPLE_DATA | Crear datos de muestra | true |
| SKIP_INIT | Omitir inicialización | false |

### Contenedor ph-database

| Variable | Descripción | Valor por defecto |
|----------|-------------|-------------------|
| POSTGRES_DB | Nombre de la base de datos | phcontrol_db |
| POSTGRES_USER | Usuario de PostgreSQL | phcontrol |
| POSTGRES_PASSWORD | Contraseña de PostgreSQL | phcontrol123 |

## Volúmenes

El sistema utiliza dos volúmenes persistentes:

1. **ph_postgres_data**: Almacena los datos de PostgreSQL
2. **ph_uploads**: Almacena los archivos subidos por los usuarios

## Red

Todos los contenedores se conectan a la red `ph-network` para comunicarse entre sí.

## Dockerfile

El archivo `Dockerfile` define la configuración del contenedor de la aplicación web:

```dockerfile
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
```

## Comandos Útiles

### Iniciar los contenedores
```bash
docker-compose up -d
```

### Detener los contenedores
```bash
docker-compose down
```

### Ver logs
```bash
docker-compose logs -f
```

### Reconstruir contenedores
```bash
docker-compose build
docker-compose up -d
```

### Ejecutar comandos en el contenedor
```bash
docker exec -it ph-control-web bash
```

### Acceder a la base de datos
```bash
docker exec -it ph-control-database psql -U phcontrol -d phcontrol_db
```

## Consideraciones de Seguridad

Para entornos de producción, se recomienda:

1. Cambiar todas las contraseñas por defecto
2. Generar una nueva SECRET_KEY
3. Deshabilitar el modo DEBUG
4. Configurar volúmenes externos para respaldos
5. Implementar HTTPS con un proxy inverso como Nginx

## Respaldos

Para respaldar la base de datos:

```bash
docker exec ph-control-database pg_dump -U phcontrol phcontrol_db > backup_$(date +%Y%m%d).sql
```

Para respaldar los archivos subidos:

```bash
docker cp ph-control-web:/app/uploads ./backups/uploads_$(date +%Y%m%d)
```