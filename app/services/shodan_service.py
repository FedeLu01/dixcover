from app.clients.shodan_client import ShodanClient
from app.models.shodan_subdomain import ShodanSubdomain
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from app.utils.log import app_logger
from app.services.base_subdomain_service import BaseSubdomainService
from app.models.subdomains_master import MasterSubdomains
from sqlalchemy import func
from sqlmodel import select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from app.config.settings import settings


class ShodanService(BaseSubdomainService):
    def __init__(self, max_depth=5, delay=5, max_workers=8):
        super().__init__(max_depth, delay, max_workers)
        # disable service if SHODAN API key is not set
        self.enabled = bool(settings.SHODAN_API_KEY)
        if self.enabled:
            self.shodan = ShodanClient()
            app_logger.info("Shodan service enabled")
        else:
            self.shodan = None
            app_logger.info("Shodan service disabled: no SHODAN_API_KEY configured")
        
    def extract_and_store_subdomains_data(self, db: Session, target_domain):        
        if not getattr(self, 'enabled', False):
            app_logger.debug(f"Shodan: skipped for {target_domain} (no API key)")
            return set()

        data = self.shodan.search_domain(target_domain)
        subdomains = set()

        app_logger.info(f"Shodan: fetched {len(data) if data else 0} items for {target_domain}")
        try:
            for sub in data: 
                if "*" in sub:
                    continue 
                full_subdomain = f"{sub}.{target_domain}"
                if self.is_valid_subdomain(full_subdomain, target_domain):
                    app_logger.debug(f"Shodan: valid subdomain {full_subdomain}")
                    subdomains.add(f"{sub}.{target_domain}") 
                    to_store = {
                        "subdomain": f"{sub}.{target_domain}",
                    }
                    self.store(db, to_store)
        except Exception as e:
            app_logger.error(f"error extracting and storing {e}")
            
        return subdomains


    def store(self, db: Session, data: dict):
        try:
            app_logger.debug(f"Shodan: upserting {data.get('subdomain')}")
            table = ShodanSubdomain.__table__
            insert_stmt = pg_insert(table).values(data)
            update_stmt = {k: insert_stmt.excluded[k] for k in data.keys() if k != 'subdomain'}
            if update_stmt:
                stmt = insert_stmt.on_conflict_do_update(index_elements=['subdomain'], set_=update_stmt)
            else:
                stmt = insert_stmt.on_conflict_do_nothing(index_elements=['subdomain'])
            db.execute(stmt)
            db.commit()

            app_logger.info(f"Shodan: upserted {data.get('subdomain')} into shodan_subdomain")

            # Upsert into master table by selecting and merging sources
            try:
                stmt = select(MasterSubdomains).where(MasterSubdomains.subdomain == data.get('subdomain'))
                master_obj = db.execute(stmt).scalars().one_or_none()
                incoming_first = data.get('detected_at')
                if master_obj is None:
                    master_obj = MasterSubdomains(
                        subdomain=data.get('subdomain'),
                        sources=['shodan'],
                        first_seen=incoming_first,
                    )
                    db.add(master_obj)
                else:
                    if 'shodan' not in (master_obj.sources or []):
                        master_obj.sources = (master_obj.sources or []) + ['shodan']
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
                app_logger.error(f"Shodan: error upserting into master: {e}")
        except IntegrityError as e:
            app_logger.debug(f'error in insert: {str(e)}')
            db.rollback()
        except Exception as e:
            db.rollback()
            app_logger.error(f'error upserting shodan subdomain: {e}')
