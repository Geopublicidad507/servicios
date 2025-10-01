# PH Control - Modo API

Sistema de gestión de propiedades horizontales configurado para usar APIs externas.

## Configuración

### API Externa
- **URL Base**: https://printed-binny-consultor351-faafa5db.koyeb.app
- **Base de datos local**: SQLite
- **Sin contenedores**: Ejecución directa con Python

## Instalación

```bash
# Instalar dependencias
pip install -r requirements_api.txt

# Configurar variables de entorno
cp .env.example .env

# Ejecutar aplicación
python run_api.py
```

## Estructura Simplificada

```
proyecto_ph_Docker/
├── app.py                 # Aplicación principal
├── config.py             # Configuración
├── run_api.py            # Script de ejecución
├── requirements_api.txt  # Dependencias simplificadas
├── utils/
│   └── api_client.py     # Cliente para API externa
├── models.py             # Modelos SQLAlchemy
├── routes/               # Rutas de la aplicación
└── templates/            # Plantillas HTML
```

## Uso

1. **Iniciar aplicación**:
   ```bash
   python run_api.py
   ```

2. **Acceder**:
   - URL: http://localhost:5003
   - Usuario: admin@phcontrol.com
   - Contraseña: admin123

## API Externa

La aplicación se conecta a:
- **Servicio**: printed-binny-consultor351-faafa5db.koyeb.app
- **Protocolo**: HTTPS
- **Formato**: JSON
- **Timeout**: 30 segundos