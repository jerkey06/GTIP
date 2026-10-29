# Núcleo del backend (área A)

Responsable: Emiliano Ponce. Este documento explica lo que el resto del equipo necesita para usar la configuración, la base de datos, los repositorios y la autenticación.

## Decisiones tomadas (pendientes de confirmar en reunión)

Se eligió la opción del ADD en cada punto abierto de [PLAN-EQUIPO.md](PLAN-EQUIPO.md). Si el equipo decide otra cosa, se cambia en una migración nueva.

| Decisión | Elegido | Dónde se nota |
|---|---|---|
| Tipo de ID | Entero `BIGINT` autoincremental (ADD §10.2) | Todas las tablas; los esquemas de la API usan `int` |
| Estados de ingesta | `pending`, `running`, `completed`, `partial`, `failed` (ADD §8.3) | `app/domain/enums.py` |
| Endpoints de lectura | Con login (ADD §12.1) | Añadir `user: CurrentUser` a cada endpoint |
| Token en el navegador | Cabecera `Authorization: Bearer <token>` | El frontend guarda el token y lo envía en cada petición |

## Estructura

```text
app/core/config.py        Variables de entorno; valida lo crítico al arrancar
app/core/security.py      Argon2id para contraseñas y JWT de acceso
app/db/base.py            Base declarativa y nombres de restricciones
app/db/session.py         get_engine(), get_sessionmaker(), get_db() para FastAPI
app/domain/enums.py       IndicatorType, IngestionStatus, TriggerType
app/domain/records.py     Contrato conectores → núcleo (VulnerabilityRecord, ObservationRecord…)
app/models/               Modelos SQLAlchemy
app/repositories/         Consultas y upserts (no hacen commit)
app/services/auth.py      Login
app/api/dependencies.py   DbSession y CurrentUser para los routers
app/api/v1/auth.py        POST /auth/login, GET /auth/me
app/cli.py                Comandos para crear y administrar usuarios
alembic/                  Migraciones
```

## Tablas

`sources`, `vulnerabilities`, `indicators`, `observations`, `ingestion_runs` y `users`. Las cinco fuentes del ADD §7.1 se insertan en la migración inicial con estos `provider_key`, que los conectores deben usar tal cual:

| `provider_key` | Habilitada al crear |
|---|---|
| `cisa_kev` | sí |
| `nvd` | sí |
| `urlhaus` | sí |
| `abuseipdb` | no (opcional) |
| `otx` | no (opcional) |

`ingestion_jobs` no está incluida: pertenece al área B (worker). Quien la cree debe hacer una migración nueva encima de `0001` y avisar en el canal antes (una sola persona genera migraciones a la vez).

## Para el área B (conectores e ingesta)

Los conectores no escriben en tablas. Devuelven registros de `app/domain/records.py` y el worker los pasa a los repositorios. Un campo en `None` significa "la fuente no aporta este dato" y **no borra** el valor guardado; así CISA KEV y NVD completan la misma vulnerabilidad sin pisarse.

```python
from app.db.session import get_sessionmaker
from app.domain.enums import IngestionStatus, TriggerType
from app.repositories import ingestion_runs, sources
from app.repositories.vulnerabilities import upsert_vulnerabilities

with get_sessionmaker()() as session:
    source = sources.get_by_provider_key(session, "cisa_kev")
    run = ingestion_runs.start_run(session, source, TriggerType.SCHEDULED)
    session.commit()  # el historial muestra la ejecución en curso
    try:
        records = ...  # list[VulnerabilityRecord] del conector
        result = upsert_vulnerabilities(session, records)
        ingestion_runs.finish_run(session, run, IngestionStatus.COMPLETED, result)
    except Exception as exc:
        session.rollback()
        ingestion_runs.finish_run(
            session, run, IngestionStatus.FAILED, error_count=1, error_summary=str(exc)
        )
    session.commit()
```

- `upsert_vulnerabilities` devuelve `UpsertResult(created, updated, unchanged)`. Repetir la misma ingesta no crea ni actualiza nada.
- `upsert_observations(session, source_id, records)` crea los indicadores que falten y deduplica por indicador + fuente + `external_id`. Sin `external_id`, guarda una observación por indicador y fuente.
- `is_known_exploited=False` solo debe enviarse tras sincronizar el catálogo KEV completo (PRD §9.2). Si no se sabe, déjalo en `None`.
- `finish_run` oculta en `error_summary` las claves de API configuradas y lo recorta a 2000 caracteres.

## Para el área C (API)

```python
from app.api.dependencies import CurrentUser, DbSession

@router.get("/vulnerabilities")
def list_vulnerabilities(db: DbSession, user: CurrentUser): ...
```

`CurrentUser` responde `401` con `WWW-Authenticate: Bearer` si falta el token, si es inválido o ha expirado, o si la cuenta está desactivada.

## Para el área D (frontend)

1. `POST /api/v1/auth/login` con `{"username": "...", "password": "..."}` devuelve `{"access_token", "token_type": "bearer", "expires_in"}` (segundos).
2. Envía `Authorization: Bearer <access_token>` en cada petición.
3. Ante un `401`, vuelve a la pantalla de login.
4. `GET /api/v1/auth/me` devuelve el usuario actual.

## Comandos

Desde `backend/`:

```bash
uv run alembic upgrade head                                 # aplica migraciones
uv run alembic revision --autogenerate -m "descripcion"     # nueva migración tras cambiar un modelo
uv run python -m app.cli create-user admin                  # pide la contraseña (mínimo 12 caracteres)
uv run python -m app.cli set-password admin
uv run python -m app.cli deactivate-user admin
```

Con Docker: `docker compose run --rm api python -m app.cli create-user admin`.

## Pruebas

- `tests/unit/`: seguridad, configuración y validación de registros. No necesitan base de datos.
- `tests/integration/` y `tests/api/test_auth.py`: necesitan PostgreSQL y `TEST_DATABASE_URL` (en `.env` o en el entorno). Sin esa variable se omiten.
- `TEST_DATABASE_URL` debe apuntar a `gtip_test`, nunca a `gtip`: las pruebas deshacen y reaplican las migraciones.
- `test_migrations_match_models` falla si alguien cambia un modelo sin crear su migración.
- En CI, GitHub Actions levanta un PostgreSQL 17 y ejecuta todas las pruebas.
