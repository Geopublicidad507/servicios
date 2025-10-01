# Guía de Instalación - PH Control

Esta guía detalla los pasos para instalar y configurar el sistema PH Control para la gestión de Propiedades Horizontales.

## Requisitos Previos

- Docker Engine (versión 20.10 o superior)
- Docker Compose (versión 2.0 o superior)
- 2GB de RAM mínimo disponible
- 10GB de espacio en disco
- Puertos disponibles:
  - 5003 (aplicación web)
  - 5435 (base de datos PostgreSQL)
  - 6380 (Redis)

## Instalación con Docker

### 1. Clonar el Repositorio

```bash
git clone https://github.com/tu-usuario/proyecto_ph.git
cd proyecto_ph
```

### 2. Configuración (Opcional)

Si deseas personalizar la configuración, puedes editar el archivo `docker-compose.yml` para modificar:

- Puertos
- Credenciales de base de datos
- Variables de entorno

### 3. Iniciar los Contenedores

```bash
docker-compose up -d
```

Este comando descargará las imágenes necesarias, construirá los contenedores y los iniciará en segundo plano.

### 4. Verificar la Instalación

```bash
docker-compose ps
```

Deberías ver tres contenedores en ejecución:
- ph-control-web
- ph-control-database
- ph-control-redis

### 5. Acceder a la Aplicación

Abre un navegador web y accede a:

```
http://localhost:5003
```

Utiliza las credenciales por defecto:
- Usuario: admin@phcontrol.com
- Contraseña: admin123

## Solución de Problemas

### Verificar Logs

Si encuentras problemas, revisa los logs de los contenedores:

```bash
docker-compose logs -f ph-web
```

### Reiniciar Contenedores

Si necesitas reiniciar los servicios:

```bash
docker-compose restart
```

### Reconstruir Contenedores

Si has realizado cambios en el código o configuración:

```bash
docker-compose down
docker-compose build
docker-compose up -d
```

### Problemas de Conexión a la Base de Datos

Verifica que el contenedor de PostgreSQL esté funcionando:

```bash
docker-compose logs ph-database
```

Puedes conectarte directamente a la base de datos para diagnóstico:

```bash
docker exec -it ph-control-database psql -U phcontrol -d phcontrol_db
```

## Respaldo y Restauración

### Crear Respaldo Manual

```bash
docker exec ph-control-database pg_dump -U phcontrol phcontrol_db > backup_$(date +%Y%m%d).sql
```

### Restaurar desde Respaldo

```bash
cat backup_YYYYMMDD.sql | docker exec -i ph-control-database psql -U phcontrol -d phcontrol_db
```

## Actualización del Sistema

Para actualizar a una nueva versión:

1. Detener los contenedores:
   ```bash
   docker-compose down
   ```

2. Actualizar el código fuente:
   ```bash
   git pull origin main
   ```

3. Reconstruir y reiniciar:
   ```bash
   docker-compose build
   docker-compose up -d
   ```

## Configuración de Correo Electrónico

Para habilitar el envío de correos, edita el archivo `docker-compose.yml` y configura las siguientes variables:

```yaml
MAIL_SERVER: smtp.gmail.com
MAIL_PORT: 587
MAIL_USE_TLS: true
MAIL_USERNAME: tu_correo@gmail.com
MAIL_PASSWORD: tu_contraseña_o_token
MAIL_DEFAULT_SENDER: tu_correo@gmail.com
```

Después de modificar, reinicia los contenedores:

```bash
docker-compose down
docker-compose up -d
```

## Soporte

Si necesitas ayuda adicional, contacta al equipo de soporte en soporte@phcontrol.com