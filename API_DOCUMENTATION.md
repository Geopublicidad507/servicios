# PH Control API - Documentación

## 🌐 URL Base
```
https://printed-binny-consultor351-faafa5db.koyeb.app
```

## 📋 Endpoints Disponibles

### 1. Información General
```http
GET /
```
**Respuesta:**
```json
{
  "message": "PH Control API - Sistema de Gestión de Propiedades Horizontales",
  "version": "1.0.0",
  "status": "OK",
  "mongodb": "connected",
  "endpoints": {
    "login": "/api/auth/login",
    "users": "/api/users",
    "health": "/health"
  }
}
```

### 2. Estado del Sistema
```http
GET /health
```
**Respuesta:**
```json
{
  "status": "OK",
  "timestamp": "2025-10-01T07:24:00.000Z",
  "mongodb": "connected"
}
```

### 3. Autenticación
```http
POST /api/auth/login
```
**Body:**
```json
{
  "email": "admin@phcontrol.com",
  "password": "admin123"
}
```
**Respuesta:**
```json
{
  "token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "user": {
    "id": "670b1234567890abcdef1234",
    "email": "admin@phcontrol.com",
    "firstName": "Administrador",
    "lastName": "General",
    "role": "admin_general"
  }
}
```

### 4. Lista de Usuarios
```http
GET /api/users
```
**Headers:**
```
Authorization: Bearer <token>
```
**Respuesta:**
```json
[
  {
    "id": "670b1234567890abcdef1234",
    "email": "admin@phcontrol.com",
    "firstName": "Administrador",
    "lastName": "General",
    "role": "admin_general",
    "createdAt": "2025-10-01T07:00:00.000Z"
  }
]
```

## 🔑 Credenciales por Defecto
- **Email:** admin@phcontrol.com
- **Contraseña:** admin123
- **Rol:** admin_general

## 🧪 Probar la API

### Con curl:
```bash
# Health check
curl https://printed-binny-consultor351-faafa5db.koyeb.app/health

# Login
curl -X POST https://printed-binny-consultor351-faafa5db.koyeb.app/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@phcontrol.com","password":"admin123"}'

# Get users (requiere token)
curl https://printed-binny-consultor351-faafa5db.koyeb.app/api/users \
  -H "Authorization: Bearer YOUR_TOKEN_HERE"
```

### Con Python:
```bash
python test_api.py
```

## 📊 Base de Datos
- **MongoDB Cloud:** consultor351.yv7gbsp.mongodb.net
- **Base de datos:** miDB
- **Colecciones:** users, properties, units, notifications, expenses, maintenance_tasks

## 🔒 Seguridad
- Autenticación JWT
- Tokens válidos por 24 horas
- Contraseñas hasheadas con bcrypt
- CORS habilitado

## 🚀 Estado del Deployment
- ✅ API funcionando
- ✅ MongoDB conectado
- ✅ Autenticación JWT activa
- ✅ Endpoints respondiendo correctamente