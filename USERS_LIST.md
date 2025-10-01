# Lista de Usuarios del Sistema PH Control

## 👥 Administradores Generales (2)
| Email | Nombre | Contraseña | Teléfono |
|-------|--------|------------|----------|
| admin@phcontrol.com | Administrador General | admin123 | +507 6000-0001 |
| superadmin@phcontrol.com | Super Administrador | super123 | +507 6000-0002 |

## 🏢 Administradores de PH (3)
| Email | Nombre | Contraseña | Teléfono |
|-------|--------|------------|----------|
| adminph1@phcontrol.com | Carlos Rodríguez | adminph123 | +507 6100-0001 |
| adminph2@phcontrol.com | María González | adminph123 | +507 6100-0002 |
| adminph3@phcontrol.com | José Martínez | adminph123 | +507 6100-0003 |

## 🏠 Residentes (8)
| Email | Nombre | Contraseña | Teléfono |
|-------|--------|------------|----------|
| residente1@phcontrol.com | Ana López | resident123 | +507 6200-0001 |
| residente2@phcontrol.com | Pedro Sánchez | resident123 | +507 6200-0002 |
| residente3@phcontrol.com | Laura Herrera | resident123 | +507 6200-0003 |
| residente4@phcontrol.com | Miguel Torres | resident123 | +507 6200-0004 |
| residente5@phcontrol.com | Carmen Vega | resident123 | +507 6200-0005 |
| residente6@phcontrol.com | Roberto Morales | resident123 | +507 6200-0006 |
| residente7@phcontrol.com | Patricia Jiménez | resident123 | +507 6200-0007 |
| residente8@phcontrol.com | Fernando Castro | resident123 | +507 6200-0008 |

## 🔧 Proveedores (4)
| Email | Nombre | Contraseña | Teléfono |
|-------|--------|------------|----------|
| proveedor1@phcontrol.com | Técnico Mantenimiento | provider123 | +507 6300-0001 |
| proveedor2@phcontrol.com | Empresa Limpieza | provider123 | +507 6300-0002 |
| proveedor3@phcontrol.com | Seguridad Integral | provider123 | +507 6300-0003 |
| proveedor4@phcontrol.com | Jardinería Verde | provider123 | +507 6300-0004 |

## 👤 Visitantes (2)
| Email | Nombre | Contraseña | Teléfono |
|-------|--------|------------|----------|
| visitante1@phcontrol.com | Juan Pérez | visitor123 | +507 6400-0001 |
| visitante2@phcontrol.com | Sofia Ramírez | visitor123 | +507 6400-0002 |

## 📊 Resumen Total
- **Total de usuarios:** 19
- **Administradores Generales:** 2
- **Administradores de PH:** 3
- **Residentes:** 8
- **Proveedores:** 4
- **Visitantes:** 2

## 🚀 Crear Usuarios
Para crear todos los usuarios en la base de datos:

### Opción 1: Script directo
```bash
python create_users.py
```

### Opción 2: Endpoint API
```bash
curl -X POST https://printed-binny-consultor351-faafa5db.koyeb.app/api/users/create
```

### Opción 3: Ver estadísticas
```bash
curl https://printed-binny-consultor351-faafa5db.koyeb.app/api/users/stats
```