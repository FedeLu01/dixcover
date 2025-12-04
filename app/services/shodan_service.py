from app.clients.shodan_client import ShodanClient
from app.models.shodan_subdomain import ShodanSubdomain
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from app.utils.log import app_logger
from app.services.base_subdomain_service import BaseSubdomainService
from app.models.subdomains_master import MasterSubdomains
from sqlalchemy import func
from sqlalchemy.dialects.postgresql import insert as pg_insert


class ShodanService(BaseSubdomainService):
    def __init__(self, max_depth=5, delay=5, max_workers=8):
        super().__init__(max_depth, delay, max_workers)
        self.shodan = ShodanClient()
        
    def extract_and_store_subdomains_data(self, db: Session, target_domain):        
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

            # upsert into master
            master_table = MasterSubdomains.__table__
            master_row = {
                'subdomain': data.get('subdomain'),
                'source': 'shodan',
                'first_seen': data.get('detected_at'),
                'last_seen': data.get('detected_at'),
            }
            m_insert = pg_insert(master_table).values(master_row)
            m_update = {
                'source': m_insert.excluded.source,
                'first_seen': func.coalesce(func.least(master_table.c.first_seen, m_insert.excluded.first_seen), m_insert.excluded.first_seen, master_table.c.first_seen),
                'last_seen': func.coalesce(func.greatest(master_table.c.last_seen, m_insert.excluded.last_seen), m_insert.excluded.last_seen, master_table.c.last_seen),
            }
            m_stmt = m_insert.on_conflict_do_update(index_elements=['subdomain'], set_=m_update)
            db.execute(m_stmt)
            db.commit()
        except IntegrityError as e:
            app_logger.debug(f'error in insert: {str(e)}')
            db.rollback()
        except Exception as e:
            db.rollback()
            app_logger.error(f'error upserting shodan subdomain: {e}')
