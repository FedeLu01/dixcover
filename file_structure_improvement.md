# Estructura de archivos mejorada

## Problemas identificados:
1. `crtsh.py` en `clients/` - debería llamarse `crtsh_client.py` para claridad
2. `dixcover.py` en `jobs/` - posible typo, debería ser `discovery.py`
3. `passive_scanner.py` en `services/` - muy específico, podría estar en `jobs/`
4. Falta estructura para tests, logs, y documentación
5. `cheatsheet.txt` en raíz debería estar en docs/

## Estructura mejorada propuesta:

```
app/
├── .venv/                      # Entorno virtual
├── .env                        # Variables de entorno
├── .gitignore                  # Git ignore
├── requirements.txt            # Dependencias
├── README.md                   # Documentación principal
├── main.py                     # Punto de entrada
├── 
├── app/
│   ├── __init__.py
│   │
│   ├── clients/                # Clientes HTTP externos
│   │   ├── __init__.py
│   │   ├── base_client.py      # Cliente base con retry, auth, etc.
│   │   ├── crtsh_client.py     # Cliente para crt.sh (renombrado)
│   │   └── shodan_client.py    # Otros clientes si los hay
│   │
│   ├── config/                 # Configuración
│   │   ├── __init__.py
│   │   ├── settings.py         # Settings principales
│   │   ├── database.py         # Config de BD
│   │   └── logging.py          # Config de logging
│   │
│   ├── controllers/            # Controladores web/API
│   │   ├── __init__.py
│   │   ├── base_controller.py  # Controlador base
│   │   ├── subdomain_controller.py
│   │   └── discovery_controller.py
│   │
│   ├── core/                   # Funcionalidades core
│   │   ├── __init__.py
│   │   ├── exceptions/
│   │   │   ├── __init__.py
│   │   │   ├── exceptions.py   # Excepciones personalizadas
│   │   │   ├── handlers.py     # Manejadores de excepciones
│   │   │   └── middleware.py   # Middleware de errores
│   │   ├── middleware/         # Middlewares generales
│   │   │   ├── __init__.py
│   │   │   ├── auth.py
│   │   │   ├── rate_limit.py
│   │   │   └── logging.py
│   │   └── utils/              # Utilidades
│   │       ├── __init__.py
│   │       ├── validators.py
│   │       ├── helpers.py
│   │       └── decorators.py
│   │
│   ├── jobs/                   # Tareas asíncronas/background
│   │   ├── __init__.py
│   │   ├── base_job.py         # Job base
│   │   ├── discovery_job.py    # Renombrado de dixcover.py
│   │   ├── passive_scan_job.py # Movido desde services/
│   │   └── init_db_job.py      # Renombrado
│   │
│   ├── models/                 # Modelos de datos
│   │   ├── __init__.py
│   │   ├── base_model.py       # Modelo base
│   │   ├── subdomain.py
│   │   ├── certificate.py
│   │   ├── scan_result.py
│   │   └── user.py             # Si hay autenticación
│   │
│   ├── repositories/           # Nueva: Acceso a datos
│   │   ├── __init__.py
│   │   ├── base_repository.py
│   │   ├── subdomain_repository.py
│   │   └── certificate_repository.py
│   │
│   ├── routes/                 # Rutas/endpoints
│   │   ├── __init__.py
│   │   ├── api/                # API routes
│   │   │   ├── __init__.py
│   │   │   ├── v1/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── subdomains.py
│   │   │   │   └── discovery.py
│   │   │   └── health.py       # Health checks
│   │   └── web/                # Web routes (si hay frontend)
│   │       ├── __init__.py
│   │       └── dashboard.py
│   │
│   ├── services/               # Lógica de negocio
│   │   ├── __init__.py
│   │   ├── base_service.py     # Servicio base
│   │   ├── subdomain_service.py
│   │   ├── certificate_service.py
│   │   ├── discovery_service.py
│   │   └── database_service.py # Renombrado de database.py
│   │
│   └── views/                  # Respuestas/Templates
│       ├── __init__.py
│       ├── serializers/        # Para APIs
│       │   ├── __init__.py
│       │   ├── subdomain_serializer.py
│       │   └── certificate_serializer.py
│       └── templates/          # Si hay frontend web
│           ├── base.html
│           └── dashboard.html
│
├── docs/                       # Documentación
│   ├── README.md
│   ├── api.md                  # Documentación de API
│   ├── cheatsheet.md           # Movido aquí
│   └── deployment.md
│
├── logs/                       # Logs (git ignored)
│   ├── app.log
│   └── error.log
│
├── scripts/                    # Scripts de utilidad
│   ├── setup.py               # Setup inicial
│   ├── migrate.py             # Migraciones
│   └── seed.py                # Datos de prueba
│
└── tests/                      # Tests
    ├── __init__.py
    ├── conftest.py             # Configuración de pytest
    ├── unit/                   # Tests unitarios
    │   ├── test_clients/
    │   ├── test_services/
    │   └── test_models/
    ├── integration/            # Tests de integración
    │   ├── test_api/
    │   └── test_jobs/
    └── fixtures/               # Datos de prueba
        └── sample_data.json
```

## Cambios específicos recomendados:

### 1. Renombrar archivos:
- `clients/crtsh.py` → `clients/crtsh_client.py`
- `jobs/dixcover.py` → `jobs/discovery_job.py`
- `jobs/init_db.py` → `jobs/init_db_job.py`
- `services/database.py` → `services/database_service.py`

### 2. Mover archivos:
- `services/passive_scanner.py` → `jobs/passive_scan_job.py`
- `cheatsheet.txt` → `docs/cheatsheet.md`

### 3. Agregar nuevas carpetas:
- `repositories/` - Para separar acceso a datos de lógica de negocio
- `tests/` - Imprescindible para cualquier proyecto serio
- `docs/` - Documentación centralizada
- `scripts/` - Scripts de utilidad
- `logs/` - Para logs (git ignored)

### 4. Mejorar estructura interna:
- Crear clases base para cada capa
- Separar rutas de API en versiones
- Agregar middleware específico
- Implementar serializers para APIs

## Beneficios de esta estructura:

1. **Escalabilidad**: Fácil agregar nuevos clientes, servicios, etc.
2. **Mantenibilidad**: Responsabilidades claras por carpeta
3. **Testabilidad**: Estructura preparada para tests
4. **Separación de responsabilidades**: Cada capa tiene su propósito
5. **Consistency**: Convenciones de nombres claras

¿Te gustaría que implemente alguna parte específica de esta reestructuración o que profundice en algún aspecto?