from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from app.clients.virus_total_client import VirusTotalClient
from app.models.virus_total_subdomain import VirusTotalSubdomain
from app.utils.log import app_logger
from app.services.base_subdomain_service import BaseSubdomainService
from app.models.subdomains_master import MasterSubdomains
from sqlalchemy import func
from sqlmodel import select
from sqlalchemy.dialects.postgresql import insert as pg_insert

import math
import time


class VirusTotalService(BaseSubdomainService):
    def __init__(self, delay=1):
        super().__init__(delay)
        from app.config.settings import settings
        # disable service if no API key configured
        self.enabled = bool(settings.VIRUS_TOTAL_API_KEY)
        if not self.enabled:
            app_logger.info("VirusTotal service disabled: no VIRUS_TOTAL_API_KEY configured")

    def extract_subdomains_data(self, data, target_domain, db: Session):
        subdomains = set()
        raw_subdomains = data['data']
        app_logger.debug(f"VirusTotal: extracting {len(raw_subdomains)} items for {target_domain}")
        try:
            for sub in raw_subdomains:
                if sub['type'] == 'domain':
                    subdomain = sub['id']
                    if self.is_valid_subdomain(subdomain, target_domain):
                        app_logger.debug(f"VirusTotal: valid subdomain extracted: {subdomain}")
                        subdomains.add(subdomain)
                        to_store = {
                            "subdomain": subdomain,
                        }
                        self.store_subdomains_data(db, to_store)
        except Exception as e:
            app_logger.error(f"error extracting and storing {e}")
        return subdomains

    def search_subdomains(self, db: Session, domain):
        if not getattr(self, 'enabled', False):
            app_logger.debug(f"VirusTotal: skipped for {domain} (no API key)")
            return set()

        virus_total_client = VirusTotalClient()
        app_logger.info(f"VirusTotal: starting search for {domain}")
        all_subdomains = set()
        next_url = None
        pages = 0
        MAX_PAGES = 0
        
        while True:
            if pages > MAX_PAGES:
                app_logger.warning(f"reached max pages ({MAX_PAGES}) for domain {domain}")
                break

            # prefer following the full `links.next` URL returned by VirusTotal when available
            data = virus_total_client.search_domain(domain, next_url=next_url)
            app_logger.debug(f"VirusTotal: page={pages} data_present={bool(data)}")
            
            # metadata to create max pages to request
            MAX_PAGES = math.ceil(data.get('meta', {}).get('count', 0) / 40)
            
            if not data:
                break

            # extract and store subdomains from this page
            try:
                page_subs = self.extract_subdomains_data(data, domain, db)
                all_subdomains.update(page_subs)
                app_logger.info(f"VirusTotal: page {pages} added {len(page_subs)} subdomains for {domain}")
            except Exception as e:
                app_logger.error(f"error processing page {pages} for {domain}: {e}")

            # prefer the `next` link (includes both limit and cursor) if VirusTotal provides it
            links = data.get('links', {}) if isinstance(data, dict) else {}
            next_link = links.get('next')

            if next_link:
                # set next_url to the absolute URL
                next_url = next_link
                app_logger.debug(f"VirusTotal: next page link found: {next_url}")

            # if no next_url, no more pages
            if not next_url:
                break

            # polite delay between paged requests
            time.sleep(self.delay)
            
            pages += 1
            
        return all_subdomains
                            

    def store_subdomains_data(self, db: Session, data: dict):
        try:
            app_logger.debug(f"VirusTotal: upserting subdomain {data.get('subdomain')}")
            table = VirusTotalSubdomain.__table__
            insert_stmt = pg_insert(table).values(data)
            update_stmt = {k: insert_stmt.excluded[k] for k in data.keys() if k != 'subdomain'}
            if update_stmt:
                stmt = insert_stmt.on_conflict_do_update(index_elements=['subdomain'], set_=update_stmt)
            else:
                stmt = insert_stmt.on_conflict_do_nothing(index_elements=['subdomain'])
            db.execute(stmt)
            db.commit()
            app_logger.info(f"VirusTotal: upserted {data.get('subdomain')} into virus_total_subdomain")

            # Upsert into master via Python-level merge so `sources` becomes a list
            try:
                stmt = select(MasterSubdomains).where(MasterSubdomains.subdomain == data.get('subdomain'))
                master_obj = db.execute(stmt).scalars().one_or_none()
                incoming_first = data.get('first_seen') or data.get('detected_at')
                if master_obj is None:
                    master_obj = MasterSubdomains(
                        subdomain=data.get('subdomain'),
                        sources=['virustotal'],
                        first_seen=incoming_first,
                    )
                    db.add(master_obj)
                else:
                    if 'virustotal' not in (master_obj.sources or []):
                        master_obj.sources = (master_obj.sources or []) + ['virustotal']
                    if incoming_first:
                        try:
                            if master_obj.first_seen is None or incoming_first < master_obj.first_seen:
                                master_obj.first_seen = incoming_first
                        except Exception:
                            pass
                    db.add(master_obj)
                db.commit()
            except Exception as e:
                db.rollback()
                app_logger.error(f"VirusTotal: error upserting into master: {e}")
        except IntegrityError:
            db.rollback()
        except Exception as e:
            db.rollback()
            app_logger.error(f'error upserting virustotal rows: {e}')
