# 🏢 PH Control

## Sistema Integral de Gestión de Propiedades Horizontales

[![Estado del Proyecto](https://img.shields.io/badge/Estado-Desarrollo-green.svg)](https://github.com/Geopublicidad507/servicios)
[![Licencia](https://img.shields.io/badge/Licencia-MIT-blue.svg)](LICENSE)
[![Tecnología](https://img.shields.io/badge/TypeScript-Node.js-blue.svg)](https://nodejs.org/)

> **PH Control** es una plataforma completa para la administración y gestión de Propiedades Horizontales en Panamá, diseñada específicamente para cumplir con los requisitos de la **Ley 284 de Propiedad Horizontal**.

### 🌟 Características Destacadas

- 📊 **Dashboard Ejecutivo** con métricas en tiempo real
- 💰 **Gestión Financiera Completa** con reportes automáticos
- 📧 **Sistema de Comunicación** integrado
- 🔧 **Módulo de Mantenimiento** con seguimiento
- 🔒 **Control de Acceso y Seguridad**
- ⚖️ **Cumplimiento Legal** certificado
- 📄 **Gestión Documental** digital

### 🚀 Demo en Vivo

[![Deployed on Koyeb](https://img.shields.io/badge/Deployed%20on-Koyeb-blue.svg)](https://awkward-gwendolen-consultor351-b4be20ea.koyeb.app/)

**Accede a la aplicación en producción:** [PH Control Live](https://awkward-gwendolen-consultor351-b4be20ea.koyeb.app/)

> **Nota:** Esta es la aplicación oficial de PH Control desplegada en Koyeb. La URL anterior (ph.conectandopersonas.life) corresponde a un sitio web diferente.

### 📋 Módulos del Sistema

| Módulo | Descripción | Estado |
|--------|-------------|--------|
| 💰 **Financiero** | Control de ingresos, gastos y reportes | ✅ Completo |
| 👥 **Residentes** | Gestión de propietarios y residentes | ✅ Completo |
| 🏢 **Propiedades** | Administración de unidades y PH | ✅ Completo |
| 📧 **Comunicación** | Notificaciones y avisos | ✅ Completo |
| 🔧 **Mantenimiento** | Órdenes de trabajo y seguimiento | ✅ Completo |
| 🔒 **Seguridad** | Control de acceso y visitantes | ✅ Completo |
| ⚖️ **Legal** | Cumplimiento normativo | ✅ Completo |
| 📊 **Reportes** | Dashboard y analytics | ✅ Completo |

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

- Node.js 18+ y npm
- Puerto 3000 disponible para la API
- MongoDB (local o en la nube)

## 🚀 Instalación Rápida

### Prerrequisitos
- Node.js 18+
- npm
- Git

### Instalación

1. **Clonar el repositorio**
   ```bash
   git clone https://github.com/Geopublicidad507/servicios.git
   cd servicios
   ```

2. **Instalar dependencias**
   ```bash
   npm install
   ```

3. **Ejecutar en modo desarrollo**
   ```bash
   npm run dev
   ```

4. **Acceder a la API**
   ```
   🌐 http://localhost:3000
   ```

### 🔧 Configuración de Desarrollo

Para desarrollo local:
```bash
# Instalar dependencias
npm install

# Ejecutar en modo desarrollo (con hot reload)
npm run dev

# O ejecutar versión compilada
npm run build
npm start
```


## 🛠️ Tecnologías Utilizadas

### Backend
- **📘 TypeScript** con **Node.js** y **Express**
- **🗄️ MongoDB** con **Mongoose** ODM
- **🔐 JWT** para autenticación
- **🛡️ Helmet** y **CORS** para seguridad
- **⚡ Express Rate Limit** para control de tasa

### Frontend
- **🎨 Bootstrap 5** para UI responsiva
- **📊 Chart.js** para gráficos y analytics
- **⚡ JavaScript ES6+** con AJAX
- **🎯 jQuery** para interactividad

### DevOps & Deployment
- **📦 npm** para gestión de dependencias
- **🔨 TypeScript Compiler** para compilación
- **☁️ Koyeb** para deployment en la nube
- **🔄 GitHub Actions** para CI/CD

### Utilidades
- **🔐 bcryptjs** para hashing de contraseñas
- **📝 express-validator** para validación
- **📊 Mongoose** para modelado de datos

## 📁 Arquitectura del Proyecto

```
ph-control/
├── 📁 src/             # Código fuente TypeScript
│   ├── routes/         # Rutas de la API
│   │   ├── auth.ts     # Autenticación
│   │   ├── users.ts    # Gestión de usuarios
│   │   └── properties.ts # Gestión de propiedades
│   ├── models/         # Modelos de MongoDB
│   ├── middleware/     # Middleware personalizado
│   └── utils/          # Utilidades
├── 📁 templates/       # Plantillas HTML (opcional)
├── 📁 static/          # Archivos estáticos
├── 📁 dist/            # Código compilado
├── 📋 package.json     # Dependencias y scripts
├── 📋 tsconfig.json    # Configuración TypeScript
└── 🚀 src/server.ts    # Punto de entrada
```

## 🤝 Contribución

1. Fork el proyecto
2. Crea tu rama de feature (`git checkout -b feature/AmazingFeature`)
3. Commit tus cambios (`git commit -m 'Add some AmazingFeature'`)
4. Push a la rama (`git push origin feature/AmazingFeature`)
5. Abre un Pull Request

## 📞 Soporte

Para soporte técnico o consultas:
- 📧 **Email**: soporte@phcontrol.com
- 🐛 **Issues**: [GitHub Issues](https://github.com/Geopublicidad507/servicios/issues)
- 📖 **Documentación**: [Wiki](https://github.com/Geopublicidad507/servicios/wiki)

## 📜 Licencia

Este proyecto está licenciado bajo la **Licencia MIT** - ver el archivo [LICENSE](LICENSE) para más detalles.

---

<div align="center">
  <p>Desarrollado con ❤️ para la comunidad de Propiedades Horizontales de Panamá</p>
  <p>
    <a href="https://awkward-gwendolen-consultor351-b4be20ea.koyeb.app/">🌐 Demo en Vivo</a> •
    <a href="https://github.com/Geopublicidad507/servicios">📂 Código Fuente</a> •
    <a href="https://github.com/Geopublicidad507/servicios/issues">🐛 Reportar Bug</a>
  </p>
  <p><small>🚀 Desplegado en <a href="https://www.koyeb.com">Koyeb</a> • 📍 Panamá 🇵🇦</small></p>
</div>