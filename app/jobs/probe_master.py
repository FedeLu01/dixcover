from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from typing import List, Optional

from sqlmodel import select

from app.services.database import SessionLocal
from app.models.subdomains_master import MasterSubdomains
from app.models.alive_subdomain import AliveSubdomain
from app.services.prober_service import ProberService
from app.clients.base_http_client import BaseHTTPClient
from app.utils.log import app_logger
from app.config.settings import settings
from app.services.notifier import notifier


DEFAULT_WORKERS = getattr(settings, "PROBER_MAX_WORKERS", 20)


def probe_master(
    max_workers: int = DEFAULT_WORKERS,
    limit: Optional[int] = None,
    http_client: Optional[object] = None,
    ports: Optional[List[int]] = None,
) -> List[dict]:
    """Probe all subdomains in `subdomains_master` and update probing columns.

    - Fetches subdomains from DB
    - Probes them concurrently (ThreadPoolExecutor)
    - Updates `is_alive`, `last_checked`, and `last_alive` when appropriate

    Returns list of probe result dicts (see ProberService.probe)
    """

    app_logger.info("probe_master.start", max_workers=max_workers, limit=limit)

    # Fetch subdomains as plain strings (no session-bound objects in threads)
    session = SessionLocal()
    try:
        # Select all subdomains from master table (limit can be used to cap work)
        q = select(MasterSubdomains)
        if limit:
            rows = session.execute(q.limit(limit)).scalars().all()
        else:
            rows = session.execute(q).scalars().all()
        subdomains = [r.subdomain for r in rows]
    finally:
        session.close()

    if not subdomains:
        app_logger.info("probe_master.no_subdomains")
        return []

    # if no http_client passed, create a default BaseHTTPClient instance
    if http_client is None:
        # BaseHTTPClient requires a base_url; we pass empty string because
        # ProberService uses full URLs when calling client's session.request.
        http_client = BaseHTTPClient(base_url="", timeout=getattr(settings, "PROBER_TIMEOUT", 5.0), max_retries=getattr(settings, "PROBER_MAX_RETRIES", 2), retry_delay=getattr(settings, "PROBER_RETRY_DELAY", 1.0))

    prober = ProberService(timeout=getattr(settings, "PROBER_TIMEOUT", 5.0), http_client=http_client, ports=ports)

    results = []
    new_alives: List[dict] = []

    with ThreadPoolExecutor(max_workers=max_workers) as exe:
        future_to_sub = {exe.submit(prober.probe, sd): sd for sd in subdomains}
        for fut in as_completed(future_to_sub):
            sd = future_to_sub.get(fut)
            res = None
            try:
                res = fut.result()
                results.append(res)
            except Exception as e:
                app_logger.error("probe_master.worker_error", subdomain=sd, error=str(e))
                continue  # Skip processing if probe failed

            # Persist each result immediately in its own session to avoid losing successes
            if res is None:
                continue
                
            try:
                r = res
                sd = r["subdomain"]
                is_alive = r.get("is_alive", False)
                probed_at = r.get("probed_at", datetime.now())

                writer = SessionLocal()
                try:
                    stmt = select(MasterSubdomains).where(MasterSubdomains.subdomain == sd)
                    obj = writer.execute(stmt).scalars().one_or_none()
                    if obj is None:
                        app_logger.warning("probe_master.missing_in_db", subdomain=sd)
                    else:
                        # We no longer track `last_checked` or `is_alive` in master
                        # Only update `last_alive` when a probe reports reachable
                        if is_alive:
                            obj.last_alive = probed_at
                        writer.add(obj)

                    # maintain alive_subdomains table: upsert when alive
                    if is_alive:
                        a_stmt = select(AliveSubdomain).where(AliveSubdomain.subdomain == sd)
                        alive_obj = writer.execute(a_stmt).scalars().one_or_none()
                        if alive_obj is None:
                            alive_obj = AliveSubdomain(
                                subdomain=sd,
                                probed_at=probed_at,
                                last_alive=probed_at,
                                status_code=r.get("status_code"),
                            )
                            writer.add(alive_obj)
                            # Defer notifications until after all probes are processed
                            new_alives.append({
                                "subdomain": sd,
                                "status": r.get("status_code"),
                                "probed_at": probed_at,
                            })
                        else:
                            alive_obj.probed_at = probed_at
                            alive_obj.last_alive = probed_at
                            alive_obj.status_code = r.get("status_code")
                            writer.add(alive_obj)

                    writer.commit()
                except Exception as e:
                    writer.rollback()
                    app_logger.error("probe_master.commit_error", subdomain=sd, error=str(e))
                finally:
                    writer.close()
            except Exception as e:
                # defensive: continue processing other futures, but log unexpected errors
                app_logger.warning("probe_master.unexpected_error", subdomain=sd if 'sd' in locals() else 'unknown', error=str(e))

    app_logger.info("probe_master.finished", total=len(results), new_alives_count=len(new_alives))

    # Send batched notifications for any newly discovered alive subdomains
    if new_alives:
        try:
            app_logger.debug("probe_master.sending_notifications", count=len(new_alives))
            notifier.notify_new_alives(new_alives)
            app_logger.info("probe_master.notifications_sent", count=len(new_alives))
        except Exception as e:
            app_logger.error("notifier.batch_error", error=str(e))
    else:
        app_logger.debug("probe_master.no_new_alives")
    
    return results


if __name__ == "__main__":
    # quick runner for manual execution
    res = probe_master()
    print(f"Probed: {len(res)} subdomains")
