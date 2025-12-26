# Changelog

All notable changes to this project will be documented in this file.

The format is based on "Keep a Changelog" and the project is maintained under Semantic Versioning.

## [Unreleased]

## [0.2.0] - 2025-12-26
### Added
- New `GET /domains/data` endpoint for read-only access to collected subdomain data
- Support for querying both master subdomains (`all_subdomains`) and alive probe results (`alive_subdomain`)
- Page-based pagination with configurable `page` and `per_page` parameters (default 50, max 100 per page)
- Pagination metadata in response headers (`X-Page`, `X-Per-Page`, `X-Total-Count`)
- HATEOAS-style links in response (`self` and `next` URLs for navigation)
- `DataConsumeService` with static methods for efficient database queries and pagination

## [0.1.0] - 2025-12-23
### Added
- Initial MVP release of Dixcover: an API-focused subdomain reconnaissance sensor.
- Data collection from multiple sources: `crt.sh`, Shodan, AlienVault OTX, VirusTotal.
- Master table to consolidate unique subdomains and preserve source lists.
- Scheduled daily discovery scans and a daily probe job (APScheduler with SQL jobstore).
- Concurrent liveness probing with configurable worker pool.
- Notifier with Slack and Discord webhook integrations; batched notifications for new alive subdomains.
- Basic FastAPI endpoints to trigger discovery and manual probe runs.
- `docker-compose.yml` for local development (Postgres + app).