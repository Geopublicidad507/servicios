Desarrollo de aplicación integral para la gestión de Propiedades Horizontales (PH)
Diseña y desarrolla una aplicación web responsive, segura y escalable para la administración y gestión de Propiedades Horizontales (PH), orientada a cumplir con las necesidades legales y operativas de la administración de PH en Panamá, con especial énfasis en el cumplimiento de la Ley 284 de Propiedad Horizontal.

✅ Características y módulos funcionales requeridos:
1. Gestión Financiera
Registro y control de cuotas de mantenimiento, alquileres, penalizaciones y otros ingresos.

Gestión y clasificación de gastos operativos: mantenimiento, limpieza, seguridad, servicios públicos, etc.

Elaboración de presupuestos anuales y mensuales con seguimiento de ejecución.

Reportes financieros automáticos: estados de resultados, balances, flujo de caja.

generación de recibos de pagos.

Generación automática de recibos, facturas y morosidad.

2. Comunicación
Módulo de notificaciones masivas por correo electrónico y dentro de la app.

Panel de avisos y noticias para mantener informados a los residentes.

Foro interno o chat comunitario para consultas y discusiones entre propietarios/administración.

Gestión de solicitudes y reclamos con seguimiento por ticket y estados.

3. Mantenimiento
Programación y registro de mantenimiento preventivo y correctivo.

Seguimiento de ordenes de trabajo, proveedores y fechas de ejecución.

Checklists y evidencias (fotos) por tarea realizada.

Alerta automática para próximas tareas y mantenimiento recurrente.

4. Seguridad y Control de Acceso
Registro de entradas y salidas de visitantes.

Integración con cámaras IP del PH.

Generación de reportes de incidencias o eventos sospechosos.

Módulo para protocolos de emergencia y alertas en tiempo real.

5. Cumplimiento Legal
Módulo de gestión legal, con plantillas para convocatorias, actas y contratos.

Validación de cumplimiento de la Ley 284 y reglamentos internos.

Registro y control de asambleas de copropietarios (convocatorias, quórum, votaciones).

Generación de minutas y documentos legales firmados digitalmente. (cada reunión programada debe tener su minuta.)

6. Documentación Digital y Archivos
Repositorio estructurado para planos, actas, contratos, reglamentos internos, etc.

Búsqueda avanzada por tipo de documento, fecha, nombre o etiquetas.

Control de versiones, acceso restringido por roles y respaldo automático en la nube.

Firma electrónica y trazabilidad de accesos a cada documento.

🔒 Requisitos Técnicos

Aplicación web responsive.

Backend escalable completo ajustado a la aplicacion.

Base de datos relacional (PostgreSQL) + almacenamiento de archivos (S3 o similar).

Seguridad: autenticación JWT, cifrado de datos sensibles, roles de usuario.

Dashboard moderno con gráficos y visualizaciones (Chart.js, Recharts).

Multicompañía: permitir la administración de múltiples PH desde una sola plataforma.

👥 Tipos de usuario
Administrador General: acceso total a todos los módulos.

Administrador de PH: gestiona una o varias propiedades específicas.

Propietario / Residente: visualiza sus cuotas, reclamos, documentos y votaciones.

Proveedor / Mantenimiento: acceso controlado a órdenes de trabajo.

Visitante: acceso temporal mediante enlace.

📈 Extras 
Panel con indicadores clave de desempeño (KPIs).

Módulo de encuestas para votaciones comunitarias.

Soporte para multilenguaje (español, inglés).

Soporte técnico por ticket.
+
## 🧠 Tecnologías Base Requeridas

uso de Docker compose y base de datos ajustada a la solicitud.
Flask y templeates del backend
puerto de la app 5003
puerto de la base de datos 5435
puerto redis 6380
no nginx


| Tecnología | Clasificación | Uso principal                                                                 |
| ---------- | ------------- | ----------------------------------------------------------------------------- |
| Bootstrap  | Frontend      | Diseño y estilo de páginas web con componentes CSS y JS reutilizables.        |
| Python     | Backend       | Desarrollo de lógica del servidor, APIs REST, procesamiento de datos.   |
| - PostgreSQL recomendado   | Base de datos | Sistema de almacenamiento embebido, ideal para soluciones locales y ligeras. |