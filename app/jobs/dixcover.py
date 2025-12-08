from app.services.database import SessionLocal
from app.models.domain_requested import DomainRequested
from app.utils.log import app_logger
from app.services.crtsh_service import CrtshService
from app.services.otx_service import OtxService
from app.services.shodan_service import ShodanService
from app.services.virus_total_service import VirusTotalService
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor, as_completed


def run_scan(domain: str, scheduled: bool = False):
    """
    run a full scan for `domain` across services.
    if `scheduled` is True, ensure the DomainRequested row has `scheduled=True`.
    this function is intended to be called by the scheduler (and can be called
    from the endpoint via BackgroundTasks as well).
    """
    app_logger.info(f"job: run_scan start {domain} scheduled={scheduled}")
    db = SessionLocal()
    try:
        # ensure there's a DomainRequested row marking this domain as scheduled
        try:
            existing = db.query(DomainRequested).filter(DomainRequested.domain == domain).first()
            if scheduled:
                if not existing:
                    lock = DomainRequested(domain=domain, scheduled=True)
                    db.add(lock)
                    db.commit()
                else:
                    existing.scheduled = True
                    db.add(existing)
                    db.commit()
            else:
                # if not called by scheduler, create/refresh a short-lived lock
                if not existing:
                    lock = DomainRequested(domain=domain)
                    db.add(lock)
                    db.commit()
                else:
                    existing.time_to_zero = datetime.now() + timedelta(minutes=15)
                    db.add(existing)
                    db.commit()
        except Exception as e:
            db.rollback()
            app_logger.debug(f"job: error ensuring DomainRequested lock: {e}")

        # run services in parallel threads
        services = [
            (CrtshService(), 'recursive_search'),
            (OtxService(), 'extract_and_store_data'),
            (ShodanService(), 'extract_and_store_subdomains_data'),
            (VirusTotalService(), 'search_subdomains'),
        ]

        futures = []
        with ThreadPoolExecutor(max_workers=4) as executor:
            for svc, method_name in services:
                method = getattr(svc, method_name)
                futures.append(executor.submit(_safe_call, method, db, domain))

            # wait for completion and collect errors
            for fut in as_completed(futures):
                try:
                    fut.result()
                except Exception as e:
                    app_logger.error(f"job: service error for {domain}: {e}")

        app_logger.info(f"job: run_scan finished {domain}")
    finally:
        db.close()


def _safe_call(fn, db, domain):
    try:
        return fn(db, domain)
    except TypeError:
        # Some service signatures expect different args (defensive)
        try:
            return fn(domain)
        except Exception as e:
            raise