# GTIP — Global Threat Intelligence Platform

Plataforma web que centraliza inteligencia pública de amenazas (CISA KEV, NVD, URLhaus y, opcionalmente, AbuseIPDB y OTX), la normaliza y la expone mediante una API FastAPI y un frontend React.

- Requisitos de producto: [docs/PRD — GTIP.md](docs/PRD%20—%20GTIP.md)
- Arquitectura: [docs/ADD — GTIP.md](docs/ADD%20—%20GTIP.md)
- Plan de trabajo del equipo: [docs/PLAN-EQUIPO.md](docs/PLAN-EQUIPO.md)
- Cómo trabajar con Git: [CONTRIBUTING.MD](CONTRIBUTING.MD)

## Estructura

```text
backend/    API FastAPI + worker de ingesta (Python, uv)
frontend/   React + TypeScript (Vite)
compose.yaml  PostgreSQL + api + worker
```

## 1. Herramientas necesarias (una sola vez)

| Herramienta | Versión | Instalación en Windows |
|---|---|---|
| Git | reciente | `winget install Git.Git` |
| Python | 3.12 o superior (usamos 3.13) | `winget install Python.Python.3.13` |
| uv | reciente | `winget install astral-sh.uv` |
| Node.js | 24 LTS | `winget install OpenJS.NodeJS.LTS` |
| WSL2 | — | `wsl --install` en PowerShell como administrador, y reiniciar |
| Docker Desktop | reciente | `winget install Docker.DockerDesktop` (después de WSL2) |
| VS Code | reciente | `winget install Microsoft.VisualStudioCode` |

En Mac usa `brew` con los mismos paquetes; en Linux, el gestor de tu distribución y Docker Engine.

Al abrir el repo, VS Code te sugerirá las extensiones recomendadas (`.vscode/extensions.json`). Acéptalas.

## 2. Primer arranque

```bash
git clone https://github.com/jerkey06/GTIP.git
cd GTIP
cp .env.example .env
```

### Base de datos (Docker)

```bash
docker compose up -d db
```

### Backend

```bash
cd backend
uv sync
uv run uvicorn app.main:app --reload
```

Comprueba que responde en http://localhost:8000/api/v1/health y que la documentación OpenAPI está en http://localhost:8000/docs.

### Frontend

```bash
cd frontend
npm install
npm run dev
```

Abre http://localhost:5173. Las llamadas a `/api` se reenvían al backend en el puerto 8000.

### Todo con Docker

```bash
docker compose up --build
```

## 3. Comandos de calidad (antes de cada PR)

Backend, desde `backend/`:

```bash
uv run ruff check .
uv run ruff format .
uv run pytest
```

Frontend, desde `frontend/`:

```bash
npm run lint
npm run build
```

GitHub Actions ejecuta estos mismos comandos en cada push y pull request a `dev` y `main`.

## 4. Añadir dependencias

- Python: `uv add <paquete>` (o `uv add --dev <paquete>`). Sube también `uv.lock`.
- Frontend: `npm install <paquete>`. Sube también `package-lock.json`.
