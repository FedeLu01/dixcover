from typing import List, Dict, Optional, Any
from fastapi import APIRouter, Depends, HTTPException, Response, Request
from sqlalchemy.orm import Session

from app.services.database import get_db
from app.middleware.security import Security
from app.schemas.data_consume import DataConsumeRequest, SubdomainOut, AliveOut
from app.services.data_consume_service import DataConsumeService
from app.services.pagination_cache import cache as pagination_cache
import json
import base64
from urllib.parse import urlencode, urljoin

router = APIRouter(tags=["Data_Consume"])


@router.post("/domains/data")
def domain_data(
    payload: DataConsumeRequest,
    response: Response,
    request: Request,
    page: int = 0,
    per_page: int = 50,
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """Return either `all` (master subdomains) or `alive` rows for a provided domain.

    Controller responsibilities are intentionally small:
    - Validate and sanitize user input via `Security`.
    - Delegate DB work to `DataConsumeService`.
    - Convert ORM models to Pydantic outputs.
    """
    sec = Security()

    # validate domain shape
    if not sec.is_valid_domain(payload.domain):
        raise HTTPException(status_code=400, detail=f"invalid domain: {payload.domain}")

    # normalize domain for queries
    clean_domain = payload.domain.strip().lower()

    # bounds for pagination: default 50, max 100
    if page < 0 or per_page < 1 or per_page > 100:
        raise HTTPException(status_code=400, detail="invalid pagination params")

    svc = DataConsumeService()

    # decide which dataset to return
    results: List[Dict] = []
    cache_key = f"{payload.source.value}:{clean_domain}"

    # Try to load cached full list
    cached = pagination_cache.get(cache_key)
    total_count = 0
    if cached is None:
        # populate the cache by fetching all items (bounded by DB capacity)
        if payload.source.value == "all_subdomains":
            rows_all = svc.list_all_master_subdomains(db, clean_domain)
            items = [
                SubdomainOut(
                    subdomain=r.subdomain,
                    sources=r.sources or [],
                    created_at=r.created_at.isoformat() if r.created_at else None,
                ).model_dump()
                for r in rows_all
            ]
        else:
            rows_all = svc.list_all_alive_subdomains(db, clean_domain)
            items = [
                AliveOut(
                    subdomain=r.subdomain,
                    probed_at=r.probed_at.isoformat() if r.probed_at else None,
                    status_code=r.status_code,
                ).model_dump()
                for r in rows_all
            ]

        pagination_cache.set(cache_key, items)
        cached = items

    total_count = len(cached)

    # compute offset and slice
    offset = page * per_page
    results = cached[offset : offset + per_page]

    # Pagination headers: X-Page, X-Per-Page, X-Next-Page (empty if none)
    # Pagination headers: X-Page, X-Per-Page, X-Total-Count
    response.headers["X-Page"] = str(page)
    response.headers["X-Per-Page"] = str(per_page)
    response.headers["X-Total-Count"] = str(total_count)

    # Build cursor for next page (base64-encoded JSON with limit/offset)
    next_cursor = ""
    if offset + per_page < total_count:
        cursor_payload = {"limit": per_page, "offset": offset + per_page}
        next_cursor = base64.b64encode(json.dumps(cursor_payload).encode()).decode()

    # Build links (self and next). If Request available, use it to build absolute URLs.
    self_url = None
    next_url = None
    # keep domain and source in the body, but provide cursor-based next as query param
    base = str(request.url).split("?")[0]
    self_q = urlencode({"page": page, "per_page": per_page})
    self_url = f"{base}?{self_q}"
    if next_cursor:
        next_q = urlencode({"page": page + 1, "per_page": per_page, "cursor": next_cursor})
        next_url = f"{base}?{next_q}"

    response_body: Dict[str, Dict] = {
        "data": results,
        "meta": {"count": total_count, "cursor": next_cursor},
        "links": {"self": self_url or "", "next": next_url or ""},
    }

    return response_body
