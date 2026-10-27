# Plan de trabajo del equipo

El PRD y el ADD están escritos para una sola persona en 6 semanas. Este documento reparte ese mismo plan entre el equipo sin cambiar el alcance del MVP.

## Ramas

| Rama | Uso |
|---|---|
| `main` | Versión estable y demostrable. Solo recibe merges desde `dev` al cerrar un hito. |
| `dev` | Integración del equipo. Recibe los PR de las ramas personales. |
| `<tu-nombre>` | Rama de trabajo de cada integrante, creada desde `dev` (ver [CONTRIBUTING.MD](../CONTRIBUTING.MD)). |

Reglas:

- Todo cambio llega a `dev` por pull request, con al menos una revisión de otra persona y el CI en verde.
- Un PR por tarea, pequeño. Mejor 3 PR de 200 líneas que uno de 600.
- Nadie hace push directo a `main` ni a `dev`.

## Áreas de trabajo

Asigna una persona responsable por área. Si son menos de cuatro, juntad áreas (A + D y B + C funcionan bien).

| Área | Responsable | Contenido |
|---|---|---|
| A. Núcleo backend | _por asignar_ | Configuración, modelos SQLAlchemy, migraciones Alembic, repositorios, autenticación JWT/Argon2 |
| B. Conectores e ingesta | _por asignar_ | Conectores CISA KEV, NVD, URLhaus; normalización y deduplicación; worker y APScheduler; `ingestion_jobs` |
| C. API y búsqueda | _por asignar_ | Endpoints `/api/v1/*`, paginación, filtros, errores, dashboard summary |
| D. Frontend | _por asignar_ | Login, navegación, dashboard, vulnerabilidades, buscador IOC, fuentes, historial |
| Transversal | todos | Pruebas de lo que cada uno programa, documentación de su módulo |

## Calendario (del ADD §19, en paralelo)

| Semana | A. Núcleo | B. Conectores | C. API | D. Frontend |
|---|---|---|---|---|
| 1 | Config, sesión de BD, modelos `sources` y `vulnerabilities`, primera migración | Interfaz base del conector + CISA KEV con fixtures y respx | `GET /health`, `GET /vulnerabilities` sobre la BD | Layout, router, cliente API, página de vulnerabilidades con datos de ejemplo |
| 2 | Upsert idempotente de vulnerabilidades, pruebas de integración con PostgreSQL | Conector NVD (paginación, límites) | Filtros y paginación de vulnerabilidades | Tabla de vulnerabilidades conectada a la API real |
| 3 | Modelos `indicators`, `observations`, `ingestion_runs` | URLhaus + normalización de URL, IP, dominio y hash | `GET /indicators`, observaciones | Buscador IOC y detalle de indicador |
| 4 | `users` + login JWT + comando para crear usuarios | Worker que reclama `ingestion_jobs`, reintentos, estados | `POST /ingestions`, historial, `/dashboard` | Fuentes e historial de ingesta, botón de ingesta manual |
| 5 | Proteger endpoints, revisión de seguridad | APScheduler, recuperación de trabajos atascados | Pulido de errores y OpenAPI | Login, dashboard con Recharts |
| 6 | Docker Compose completo, backup con `pg_dump` | Simular fallos de fuente | Pruebas de API completas | Estados de carga y error, pruebas |

Al final de cada semana: merge de `dev` a `main` si el CI está en verde y el flujo del hito funciona.

**Hito 1 (fin de semana 1):** flujo vertical con CISA KEV, de la descarga a `GET /api/v1/vulnerabilities` con datos en PostgreSQL (PRD §26). Es la prioridad máxima; todo lo demás se construye encima.

## Contratos entre áreas

- **Frontend ↔ API:** el contrato es el OpenAPI de FastAPI (`/docs`). El área C publica los esquemas Pydantic antes de implementar la lógica, para que D no espere.
- **Conectores ↔ núcleo:** el área B devuelve modelos internos validados (Pydantic); nunca escribe en tablas directamente (ADD §6.4).
- **Modelos:** solo una persona genera migraciones Alembic a la vez. Coordinad en el canal antes de crear una para evitar dos `head`.

## Decisiones a cerrar en la primera reunión

El PRD y el ADD no coinciden en algunos detalles. Elegid una opción y actualizad el ADD:

1. **Tipo de ID:** UUID (PRD §9) o entero (ADD §10.2).
2. **Estados de ingesta:** `success` (PRD §9.5) o `completed` + `pending` (ADD §8.3).
3. **Rutas de ingesta:** `/ingestion/runs` (PRD §11) o `/ingestions` (ADD §11.2).
4. **Dashboard:** `/dashboard/summary` (PRD) o `/dashboard` (ADD).
5. **Endpoints de lectura públicos o con login:** el PRD §10.6 los permite públicos en la demo; el ADD §12.1 exige autenticación.
6. **Token en el navegador:** cookie segura o almacenamiento en el frontend (ADD §22.3).
7. **Clave NVD:** cada persona puede pedir la suya gratis en https://nvd.nist.gov/developers/request-an-api-key y ponerla en su `.env`.

## Definición de terminado (por PR)

- [ ] Funciona en local siguiendo el README.
- [ ] Tiene pruebas para la lógica nueva; los conectores se prueban con fixtures, sin llamar a la API real.
- [ ] `ruff check`, `ruff format`, `pytest`, `npm run lint` y `npm run build` pasan.
- [ ] Sin secretos en el código ni en los logs.
- [ ] Revisado por otra persona.
