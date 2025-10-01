# Guía de Solución de Problemas - PH Control

## Problemas Comunes y Soluciones

### 1. Error de Credenciales de Login

**Problema**: Los logs muestran "Invalid credentials" al intentar hacer login.

**Solución**:
```bash
# Ejecutar el script de corrección de credenciales
python fix_admin_credentials.py

# O probar las credenciales actuales
python test_credentials.py
```

**Credenciales por defecto**:
- **Administrador General**: admin@phcontrol.com / admin123
- **Administrador PH**: adminph@phcontrol.com / admin123  
- **Residente**: residente@phcontrol.com / resident123

### 2. Error de JavaScript en Notificaciones

**Problema**: Error "Unexpected token '<', "<!DOCTYPE "... is not valid JSON"

**Causa**: El endpoint de notificaciones está devolviendo HTML en lugar de JSON cuando el usuario no está autenticado.

**Solución**: Ya corregido en el código. El JavaScript ahora maneja correctamente las respuestas no-JSON.

### 3. Puerto Incorrecto

**Problema**: La aplicación corre en puerto 8000 en lugar de 5003.

**Solución**: 
- Verificar la variable de entorno `PORT=5003` en docker-compose.yml
- La aplicación debería usar automáticamente el puerto correcto

### 4. Base de Datos No Inicializada

**Problema**: Errores relacionados con tablas o usuarios faltantes.

**Solución**:
```bash
# Ejecutar inicialización completa
python init_system.py

# O inicialización simple
python init_simple.py
```

### 5. Problemas de Conexión a PostgreSQL

**Problema**: Error de conexión a la base de datos PostgreSQL.

**Solución**:
```bash
# Verificar que PostgreSQL esté corriendo
docker-compose ps

# Reiniciar servicios
docker-compose down
docker-compose up -d

# Verificar logs
docker-compose logs ph-database
```

### 6. Archivos de Upload Faltantes

**Problema**: Errores al subir archivos.

**Solución**:
```bash
# Crear directorios necesarios
mkdir -p uploads/documents uploads/receipts uploads/maintenance uploads/profiles
mkdir -p backups logs temp
```

## Comandos Útiles

### Reiniciar Aplicación
```bash
docker-compose restart ph-web
```

### Ver Logs en Tiempo Real
```bash
docker-compose logs -f ph-web
```

### Acceder al Contenedor
```bash
docker-compose exec ph-web bash
```

### Limpiar y Reconstruir
```bash
docker-compose down -v
docker-compose build --no-cache
docker-compose up -d
```

### Backup de Base de Datos
```bash
docker-compose exec ph-database pg_dump -U phcontrol phcontrol_db > backup.sql
```

### Restaurar Base de Datos
```bash
docker-compose exec -T ph-database psql -U phcontrol phcontrol_db < backup.sql
```

## Variables de Entorno Importantes

```bash
# En docker-compose.yml
PORT=5003                    # Puerto de la aplicación
DEBUG=True                   # Modo debug
CREATE_SAMPLE_DATA=true      # Crear datos de muestra
SKIP_INIT=false             # Saltar inicialización
DATABASE_URL=postgresql://...# URL de base de datos
```

## Verificación de Estado

### Verificar Servicios
```bash
curl http://localhost:5003/
```

### Verificar API
```bash
curl http://localhost:5003/api/notifications/check
```

### Verificar Base de Datos
```bash
python test_connection.py
```

## Contacto y Soporte

Si los problemas persisten:
1. Revisar los logs completos: `docker-compose logs ph-web`
2. Verificar la configuración de red y puertos
3. Comprobar que todos los servicios estén corriendo
4. Revisar las variables de entorno

## Logs Importantes

- **Aplicación**: `docker-compose logs ph-web`
- **Base de datos**: `docker-compose logs ph-database`
- **Archivos de log**: `logs/audit.log`, `logs/notifications.log`