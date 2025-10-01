# PH Control - Sistema de Gestión de Propiedades Horizontales

Sistema integral para la administración y gestión de Propiedades Horizontales (PH), orientado a cumplir con las necesidades legales y operativas de la administración de PH en Panamá, con especial énfasis en el cumplimiento de la Ley 284 de Propiedad Horizontal.

## Características Principales

### 1. Gestión Financiera
- Registro y control de cuotas de mantenimiento, alquileres, penalizaciones y otros ingresos
- Gestión y clasificación de gastos operativos
- Elaboración de presupuestos anuales y mensuales con seguimiento
- Reportes financieros automáticos
- Generación de recibos de pagos y facturas

### 2. Comunicación
- Notificaciones masivas por correo electrónico y dentro de la app
- Panel de avisos y noticias para residentes
- Foro interno para consultas y discusiones
- Gestión de solicitudes y reclamos con seguimiento por ticket

### 3. Mantenimiento
- Programación y registro de mantenimiento preventivo y correctivo
- Seguimiento de órdenes de trabajo y proveedores
- Checklists y evidencias fotográficas
- Alertas automáticas para tareas recurrentes

### 4. Seguridad y Control de Acceso
- Registro de entradas y salidas de visitantes
- Integración con cámaras IP
- Reportes de incidencias
- Protocolos de emergencia

### 5. Cumplimiento Legal
- Gestión de documentos legales y plantillas
- Validación de cumplimiento de la Ley 284
- Registro y control de asambleas
- Generación de minutas y documentos firmados digitalmente

### 6. Documentación Digital
- Repositorio estructurado para documentos
- Búsqueda avanzada
- Control de versiones y acceso restringido
- Firma electrónica y trazabilidad

## Requisitos Técnicos

- Docker y Docker Compose
- Puerto 5003 disponible para la aplicación web
- Puerto 5435 disponible para la base de datos PostgreSQL

## Instalación

1. Clonar el repositorio:
   ```
   git clone https://github.com/tu-usuario/proyecto_ph.git
   cd proyecto_ph
   ```

2. Iniciar los contenedores con Docker Compose:
   ```
   docker-compose up -d
   ```

3. Acceder a la aplicación:
   ```
   http://localhost:5003
   ```

## Credenciales por defecto

- **Administrador General**:
  - Usuario: admin@phcontrol.com
  - Contraseña: admin123

- **Administrador PH**:
  - Usuario: adminph@phcontrol.com
  - Contraseña: admin123

- **Residente**:
  - Usuario: residente@phcontrol.com
  - Contraseña: resident123

## Tecnologías Utilizadas

- **Backend**: Python con Flask
- **Frontend**: Bootstrap, HTML5, CSS3, JavaScript
- **Base de datos**: PostgreSQL
- **Contenedores**: Docker y Docker Compose
- **Gráficos**: Chart.js
- **Reportes**: ReportLab

## Estructura del Proyecto

```
proyecto_ph/
├── app.py                 # Punto de entrada de la aplicación
├── models.py              # Modelos de datos
├── routes/                # Rutas y controladores
├── templates/             # Plantillas HTML
├── static/                # Archivos estáticos (CSS, JS)
├── utils/                 # Utilidades y helpers
├── docker-compose.yml     # Configuración de Docker Compose
├── Dockerfile             # Configuración de Docker
└── requirements.txt       # Dependencias de Python
```

## Desarrollo

Para ejecutar la aplicación en modo desarrollo:

```
docker-compose up
```

Para reconstruir los contenedores después de cambios:

```
docker-compose build
docker-compose up -d
```

## Licencia

Este proyecto está licenciado bajo los términos de la licencia MIT.