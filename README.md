# OceanLearn — Backend (Flask)

API REST completa para la aplicación OceanLearn de monitoreo de vida marina.

## Estructura del proyecto

```
oceanlearn-backend/
├── app.py              ← Punto de entrada principal
├── config.py           ← Configuración (dev / prod / testing)
├── extensions.py       ← Instancia de SQLAlchemy
├── seed.py             ← Script para poblar la BD con datos de prueba
├── requirements.txt
├── .env.example        ← Plantilla de variables de entorno
├── models/
│   └── __init__.py     ← Modelos: User, Species, Zone, Observation
└── routes/
    ├── auth.py         ← /api/auth  (register, login, me, refresh)
    ├── species.py      ← /api/species
    ├── observations.py ← /api/observations
    ├── zones.py        ← /api/zones
    ├── users.py        ← /api/users
    ├── dashboard.py    ← /api/dashboard/stats
    └── reports.py      ← /api/reports  (resumen, CSV, gráficas)
```

## Instalación rápida

```bash
# 1. Clonar / descargar el proyecto
cd oceanlearn-backend

# 2. Crear entorno virtual
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate

# 3. Instalar dependencias
pip install -r requirements.txt

# 4. Configurar variables de entorno
cp .env.example .env
# Edita .env si quieres cambiar algo (opcional para desarrollo)

# 5. Poblar la base de datos con datos de prueba
python seed.py

# 6. Iniciar el servidor
python app.py
```

El servidor queda disponible en `http://localhost:5000`

---

## Endpoints disponibles

### Autenticación (`/api/auth`)
| Método | Ruta              | Descripción                    | Auth |
|--------|-------------------|--------------------------------|------|
| POST   | /register         | Crear cuenta nueva             | No   |
| POST   | /login            | Iniciar sesión → JWT           | No   |
| POST   | /refresh          | Renovar access token           | Refresh token |
| GET    | /me               | Perfil del usuario actual      | Sí   |
| PUT    | /change-password  | Cambiar contraseña             | Sí   |

### Especies (`/api/species`)
| Método | Ruta    | Descripción                      | Roles      |
|--------|---------|----------------------------------|------------|
| GET    | /       | Listar (paginado, búsqueda)      | Todos       |
| GET    | /:id    | Detalle de especie               | Todos       |
| POST   | /       | Crear especie                    | admin / investigador |
| PUT    | /:id    | Editar especie                   | admin / investigador |
| DELETE | /:id    | Eliminar especie                 | admin      |

### Observaciones (`/api/observations`)
| Método | Ruta    | Descripción                      | Roles      |
|--------|---------|----------------------------------|------------|
| GET    | /       | Listar (filtros: especie, zona…) | Todos       |
| GET    | /:id    | Detalle                          | Todos       |
| POST   | /       | Crear (soporta foto multipart)   | Todos       |
| PUT    | /:id    | Editar (propio o admin)          | Todos       |
| DELETE | /:id    | Eliminar (propio o admin)        | Todos       |

### Zonas (`/api/zones`)
| Método | Ruta  | Descripción        | Roles                |
|--------|-------|--------------------|----------------------|
| GET    | /     | Listar zonas       | Todos                 |
| POST   | /     | Crear zona         | admin / investigador |
| PUT    | /:id  | Editar zona        | admin / investigador |
| DELETE | /:id  | Eliminar zona      | admin                |

### Reportes (`/api/reports`)
| Método | Ruta              | Descripción                   |
|--------|-------------------|-------------------------------|
| GET    | /summary          | Totales y crecimiento         |
| GET    | /by-species       | Conteo por especie            |
| GET    | /by-zone          | Conteo + % por zona           |
| GET    | /monthly-trends   | Tendencia mensual (12 meses)  |
| GET    | /top-observers    | Ranking de observadores       |
| GET    | /export           | Descarga CSV                  |

Todos los reportes aceptan el query param `?period=week|month|quarter|year`.

### Dashboard (`/api/dashboard`)
| Método | Ruta   | Descripción                        |
|--------|--------|------------------------------------|
| GET    | /stats | KPIs + actividad reciente          |

---

## Autenticación

Todos los endpoints protegidos requieren el header:
```
Authorization: Bearer <access_token>
```

---

## Subida de fotos

El endpoint `POST /api/observations` acepta `multipart/form-data` con un campo `photo` (jpg, png, webp, gif — máx 10 MB). La foto se guarda en la carpeta `uploads/` y la URL se devuelve en `photo_url`.

---

## Roles de usuario

| Rol          | Permisos especiales                          |
|--------------|----------------------------------------------|
| admin        | Todo: gestión de usuarios, borrar cualquier cosa |
| investigador | Crear/editar especies y zonas                |
| educador     | Crear observaciones                          |
| estudiante   | Crear observaciones                          |
| entusiasta   | Crear observaciones                          |

---

## Migrar a PostgreSQL (producción)

1. Instalar: `pip install psycopg2-binary`
2. En `.env`: `DATABASE_URL=postgresql://user:pass@host:5432/oceanlearn`
3. Ejecutar migraciones: `flask db upgrade`
4. Iniciar con Gunicorn: `gunicorn -w 4 "app:create_app()"`
