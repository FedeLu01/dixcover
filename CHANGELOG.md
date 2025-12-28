# Changelog

All notable changes to this project will be documented in this file.

The format is based on "Keep a Changelog" and the project is maintained under Semantic Versioning.

## [Unreleased]

## [0.2.2] - 2025-12-28
### Changed
- Refactored `POST /probe` endpoint to follow best practices:
  - Improved error handling with proper HTTP status codes (202 Accepted for async operations)
  - Enhanced OpenAPI documentation with detailed descriptions and response models
  - Removed user-controllable `limit` parameter (endpoint now probes all subdomains)
- Fixed Discord notification message size issues:
  - Added Discord embed limits enforcement (description max 4096 chars, title max 256 chars)
  - Implemented truncation logic for batch notifications with "... and X more subdomains" message
  - Limited batch notifications to 50 items to prevent description overflow
  - Added mention support (`@everyone`, `@here`) to batch notifications
  - Improved timestamp handling to prevent invalid embed formats

### Fixed
- Discord webhook errors (400 status) caused by embed description exceeding 4096 character limit
- Improved error logging in probe master job with better exception tracking

## [0.2.1] - 2025-12-26
### Changed
- Improved domain validation to support multi-level TLDs (e.g., `example.com.ar`, `example.co.uk`)
- Replaced custom regex validation with `tldextract` and `validators.domain` for more robust RFC-compliant validation
- Simplified domain parsing logic by removing redundant `urlparse` usage (tldextract handles URLs, ports, and paths automatically)

### Added
- Added `tldextract==5.1.2` and `validators==0.34.0` dependencies for enhanced domain validation

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