<div align="center">
<img src=".github/assets/banner.svg" width="220" alt="dixcover logo" />
<p><strong>Dixcover</strong> - An API for <strong>subdomain discovery</strong>, <strong>liveness probing</strong>, and batched <strong>Slack/Discord</strong> notifications.</p>
</div>

---

Dixcover gathers data from multiple passive providers, consolidates results, probes hosts, and sends batched Slack/Discord alerts for newly found live subdomains. It persists findings in PostgreSQL for fast lookups and follow-up actions.

## Quickstart (Docker Compose)

This Quickstart shows the recommended Docker Compose workflow for local development.

Prerequisites: Docker and Docker Compose.

1) Clone the repo

```bash
git clone https://github.com/your-org/dixcover.git
cd dixcover
```

2) Configure env

Copy the example environment file and edit values (DB credentials, webhooks, API keys):

```bash
cp .env.example .env
# Edit .env and set DB_USER, DB_PASSWORD, DB_NAME, and any webhook/API keys
```

Example minimal `.env` values (for local dev only):

```env
# PostgreSQL
DB_HOST_IP=db
DB_USER=postgres
DB_PASSWORD=postgres
DB_NAME=dixcover_db

# Optional providers / notifiers
SHODAN_API_KEY=
VIRUS_TOTAL_API_KEY=
OTX_API_KEY=
SLACK_WEBHOOK_URL=
DISCORD_WEBHOOK_URL=
```

3) Start the database and build the web image

Start only the DB first so it has time to initialize:

```bash
docker compose up -d db
docker compose build web
```

4) Run migrations (one-off inside the `web` image)

The repository includes `./scripts/migrate.sh` which runs `alembic upgrade head` from the project root. Run it as a one-off container so migrations run with the same image code:

```bash
docker compose run --rm web ./scripts/migrate.sh
```

If the migrations succeed, start the web service:

```bash
docker compose up -d web
```

Alternative: bring up everything at once and then run migrations in a separate one-off container:

```bash
docker compose up --build -d
docker compose run --rm web ./scripts/migrate.sh
```

5) Check health & logs

Follow the web logs:

```bash
docker compose logs -f web
```

Inspect database tables (psql inside container):

```bash
docker compose exec db psql -U "$DB_USER" -d "$DB_NAME" -c "\dt"
```

6) Stop / reset (development)

Stop services:

```bash
docker compose down
```

To remove the DB volume (useful for a clean start; WARNING: destroys data):

```bash
docker compose down -v
```

Notes

- `./scripts/migrate.sh` expects Alembic to be available in the image built from `requirements.txt`. If you change dependencies, rebuild the image with `docker compose build web`.
- To rebuild the web image and restart:

```bash
docker compose up --build -d web
```

- If you prefer to run locally without Docker, a local Python Quickstart remains in the repo, but Docker Compose is the recommended flow for reproducible development.

## API

The app exposes a small set of endpoints (FastAPI). With the default configuration they are mounted at root.

- `POST /` — Start a discovery scan for a domain. Accepts a JSON body containing `domain` (e.g. `{"domain": "example.com"}`). This enqueues background discovery tasks (crt.sh, shodan, otx, virus total) and registers a daily job for the domain.
- `POST /probe` — Trigger the probing job manually. Accepts optional query param `limit` to probe only a subset of master subdomains.

Examples:

```bash
curl -X POST -H "Content-Type: application/json" -d '{"domain":"example.com"}' http://127.0.0.1:8000/

# trigger probe now
curl -X POST "http://127.0.0.1:8000/probe?limit=50"
```

You can use `yaak` too, or any other API client to call the endpoints above.

## Notifications

Notifier supports Slack and Discord via incoming webhooks. The notifier detects configured platforms by inspecting the environment variables `SLACK_WEBHOOK_URL` and `DISCORD_WEBHOOK_URL` at process startup. If present, notifications will be sent when new alive subdomains are discovered.

Behavior:
- The system will create or update `AliveSubdomain` rows when probes report a reachable host.
- During a probe run, newly-created alive rows are collected and a single batched message is sent at the end of the run (minimizes notification noise).
- Slack and Discord payloads are formatted for readability (timestamp Y-m-d H:M, subdomain, status), with guards for Slack payload size and block counts.

Optional mention controls (set via env):
- `SLACK_MENTION` — `here` or `channel` (sends `<!here>` or `<!channel>` in the Slack message)
- `DISCORD_MENTION` — `here` or `everyone` (adds `@here` or `@everyone` to the Discord message content)

Example (zsh):

```bash
export SLACK_WEBHOOK_URL="https://hooks.slack.com/services/T/..."
export SLACK_MENTION=here
export DISCORD_WEBHOOK_URL="https://discord.com/api/webhooks/..."
export DISCORD_MENTION=everyone
```

Tip: you can keep a copy of sample environment values in `.env.example` and copy it during setup.

## Configuration

All configuration values are loaded from environment variables via `app/config/settings.py` (Pydantic `BaseSettings`). Key variables:

- `DB_HOST_IP`, `DB_USER`, `DB_PASSWORD`, `DB_NAME` — PostgreSQL connection pieces
- `SHODAN_API_KEY`, `VIRUS_TOTAL_API_KEY`, `OTX_API_KEY` — provider API keys (optional)
- `SLACK_WEBHOOK_URL`, `DISCORD_WEBHOOK_URL` — notification webhook URLs (optional)

If you set an env var after the process starts you must restart the app to pick up the change (notifier reads env at import time).

## Development notes

- The scheduler uses APScheduler with an SQLAlchemy jobstore; the application's SQLAlchemy `engine` is used so jobs persist across restarts.
- Concurrency: probes run in a `ThreadPoolExecutor` (default worker pool configurable via `PROBER_MAX_WORKERS` in settings).
- The prober treats any HTTP response as "alive"; only network-level errors (DNS, timeout, connection refused) mean "not alive".
- Many models were refactored during development — if you modify models be sure to apply DB migrations.

- New helper scripts / files included in this repo:
	- `scripts/migrate.sh` — wrapper to run Alembic commands from project root (ensures PYTHONPATH is set).
	- `.env.example` — sample environment variables for local development.
	- `Dockerfile` and `docker-compose.yml` — build and run the web app and Postgres locally.

## Roadmap

- Add precise public suffix handling (accept `example.co.uk` correctly while rejecting deeper subdomains as configured)
- Improve observability (structured logs, tracing, metrics)
- Queueing and retries for notifications and provider calls
- Expand discovery sources and add passive/non-API discovery methods

## Contributing

Contributions are welcome. Please open issues for bugs and feature requests. For code contributions, open a pull request with a clear description and tests when applicable.

## License

This project is provided under the MIT License. See `LICENSE` for details.