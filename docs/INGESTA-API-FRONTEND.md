# Ingesta, API y frontend (áreas B, C y D)

Complementa a [NUCLEO-BACKEND.md](NUCLEO-BACKEND.md). Explica cómo funcionan los conectores, el worker, los endpoints y el frontend, y qué decisiones abiertas del [plan de equipo](PLAN-EQUIPO.md) se cerraron al implementarlos.

## Decisiones tomadas

| Decisión (PLAN-EQUIPO / UI §10) | Elegido | Motivo |
|---|---|---|
| Rutas de ingesta y dashboard | `/ingestions` y `/dashboard` (ADD §11.2) | Coherente con el resto del ADD |
| Estados de ingesta | `pending`, `running`, `completed`, `partial`, `failed` | Ya en `app/domain/enums.py` |
| Lectura pública o con login | Todo con login salvo `/health`, `/health/ready` y `/auth/login` | ADD §12.1 |
| Token en el navegador | `sessionStorage`, cabecera `Authorization: Bearer` | Sobrevive a recargar la pestaña pero no a cerrarla; nunca `localStorage` |
| `ingestion_jobs` | No hay tabla aparte: una fila de `ingestion_runs` en `pending` es la solicitud | El historial muestra la ingesta desde que se pide y el `POST` devuelve el id de la ejecución (UI M-01) |
| `GET /search` y `GET /sources/{id}` | Implementados | Las pantallas P-07 y P-09 los usan directamente |
| Campos KEV de la CVE (UI P-04) | Columnas `kev_*` en `vulnerabilities` | Migración `0002` |
| Parámetro de orden | `sort` con valores fijos (`-published_at`, `published_at`, `-modified_at`, `-cvss_score`, `-created_at`) | Nunca se usa texto del usuario como SQL (ADD §11.3) |
| Login con usuario o correo | Usuario | Es lo que guarda la tabla `users` |
| Reputación bajo demanda (AbuseIPDB) | No incluida | Opcional en el MVP; AbuseIPDB y OTX aparecen como fuentes deshabilitadas |

## Conectores (`app/connectors/`)

| Fuente | Qué descarga | Incremental | Clave |
|---|---|---|---|
| `cisa_kev` | Catálogo KEV completo (JSON) | No: siempre entero, así detecta CVE que salen del catálogo | No |
| `nvd` | CVE modificadas desde la última ingesta correcta (API 2.0, 2000 por página) | Sí, con 15 min de solapamiento; la primera vez, `NVD_INITIAL_DAYS`; como máximo 120 días | Opcional (`NVD_API_KEY`): de 6 s a 0,6 s entre páginas |
| `urlhaus` | URLs añadidas en los últimos 30 días (CSV `csv_recent`) | Lo decide la fuente | Opcional (`URLHAUS_AUTH_KEY`) |

Reglas comunes (`base.py`):

- HTTPX con tiempo máximo (`HTTP_TIMEOUT_SECONDS`) y `User-Agent` propio.
- Reintentos limitados (`INGESTION_MAX_RETRIES`) con espera exponencial solo para errores de conexión, `429` y `5xx`; respeta `Retry-After` hasta 60 s. Un `4xx` no se reintenta.
- Los mensajes de error no incluyen la URL completa (podría llevar una clave).
- Un registro que no supera la validación se descarta y la ejecución queda `partial` con el motivo en `error_summary`. El resto se guarda igual.
- CISA KEV solo quita la marca KEV a CVE que ya no están en el catálogo si el catálogo se descargó entero sin registros inválidos.
- La descripción corta de KEV se guarda en `kev_short_description`; `description` es la completa de NVD. Así no se pisan en cada sincronización.

Para añadir una fuente: crear `app/connectors/<fuente>.py` con una subclase de `Connector` (`provider_key`, `fetch`, opcionalmente `unavailable_reason`) y registrarla en `CONNECTORS` de `app/connectors/__init__.py`. El `provider_key` debe existir en la tabla `sources`.

## Worker (`app/ingestion/`)

```bash
uv run python -m app.ingestion.worker          # bucle con planificador
uv run python -m app.ingestion.worker --once   # procesa lo pendiente y termina (útil en desarrollo)
```

1. **Planificador** (`scheduler.py`, APScheduler): cada `<FUENTE>_INTERVAL_MINUTES` crea una solicitud `pending` con `trigger_type=scheduled`. La primera vez que arranca sin datos sincroniza enseguida; si ya hubo una ingesta correcta, respeta el intervalo aunque el worker se reinicie.
2. **Cola** (`ingestion_runs` en `pending`): la API también crea solicitudes (`trigger_type=manual`). El índice único parcial `uq_ingestion_runs_active_source` impide dos solicitudes activas de la misma fuente; la API responde `409` con `active_run_id`.
3. **Reclamación**: `claim_next_pending` usa `SELECT … FOR UPDATE SKIP LOCKED`, así varios workers no ejecutan la misma.
4. **Ejecución** (`app/services/ingestion.py`): el conector descarga sin transacción abierta; después se hace el upsert y se cierra la ejecución con sus contadores en una sola transacción. Si la fuente falla, la ejecución queda `failed` y los datos anteriores no se tocan.
5. **Recuperación**: al arrancar y en cada vuelta, las ejecuciones `running` con más de `INGESTION_STALE_AFTER_MINUTES` se marcan `failed`.

## API (`/api/v1`)

La referencia completa está en `/docs` (OpenAPI, solo fuera de producción).

| Método | Ruta | Notas |
|---|---|---|
| `GET` | `/health` | Liveness, pública |
| `GET` | `/health/ready` | Comprueba PostgreSQL; `503` si no responde. Pública |
| `POST` | `/auth/login` | `429` tras `LOGIN_RATE_LIMIT_PER_MINUTE` intentos por IP |
| `GET` | `/auth/me` | |
| `GET` | `/dashboard` | Estadísticas, estado de fuentes, distribución CVSS y actividad reciente |
| `GET` | `/sources`, `/sources/{id}` | Estado basado en la última ejecución; nunca devuelve claves |
| `GET` | `/vulnerabilities` | `q`, `is_kev`, `min_cvss`, `max_cvss`, `has_cvss`, `published_after`, `published_before`, `sort`, `page`, `page_size` |
| `GET` | `/vulnerabilities/{cve_id}` | `400` si el formato no es CVE, `404` si no está |
| `GET` | `/indicators` | `value`, `type`, `source_id`. Un valor reconocible se normaliza y se busca exacto; si no, coincidencia parcial. `422` si no encaja con `type` |
| `GET` | `/indicators/{id}`, `/indicators/{id}/observations` | Observaciones con su fuente y `source_data` |
| `POST` | `/ingestions` | `{"source_id": n}` → `202` con la ejecución `pending`; `409` si la fuente está deshabilitada o ya tiene una activa |
| `GET` | `/ingestions`, `/ingestions/{id}` | Filtros `source_id`, `status`, `trigger_type`, `requested_after`, `requested_before` |
| `GET` | `/search?q=` | Clasifica el texto (CVE, tipo de IOC o texto libre) y devuelve 5 resultados de cada grupo y la coincidencia exacta si la hay |

Los listados devuelven `{items, total, page, page_size}`; `page_size` admite hasta 100. Los errores inesperados responden `500` con `{"detail": "Error interno del servidor"}` sin trazas.

## Frontend (`frontend/src/`)

```text
api/         client.ts (fetch, token, errores), endpoints.ts (una función por endpoint), types.ts
auth/        AuthProvider, contexto de sesión y ruta protegida
layout/      Menú lateral, barra superior con búsqueda global y menú de usuario
components/  Estados de datos, badges, paginación, indicador «desactivado», modal de ingesta, gráfica
hooks/       useApi (carga, cancelación y sondeo), useUrlState (filtros en la URL)
lib/         Formato de fechas, detección de indicadores, mensajes de error, estados
pages/       Una pantalla por archivo, con el identificador del UI spec en su comentario
```

- Todas las pantallas P-01 a P-13 y el modal M-01 del [UI spec](UI%20—%20GTIP.md) están implementados.
- Los indicadores se muestran «desactivados» (`hxxp://ejemplo[.]com`), nunca como enlace; «Copiar» copia el valor original.
- Las pantallas de fuentes, historial y detalle de ejecución se actualizan solas mientras hay ingestas `pending` o `running`.
- Recharts se carga aparte, solo en el dashboard.

## Despliegue con Docker

`docker compose up --build` levanta `db`, `migrate`, `api`, `worker` y `frontend`. La aplicación queda en http://localhost:8080 (nginx sirve el frontend y reenvía `/api` a la API). La API sigue expuesta en el puerto 8000 para desarrollo.

Alternativa sin nginx: compilar el frontend y definir `FRONTEND_DIST_DIR` para que FastAPI lo sirva junto a la API (ADR-04).
