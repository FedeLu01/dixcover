from app.clients.otx_client import OtxClient
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from app.models.otx_subdomains import OtxSubdomain
from app.models.subdomains_master import MasterSubdomains
from sqlalchemy import func
from sqlmodel import select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from app.utils.log import app_logger
from app.config.settings import settings
from app.services.base_subdomain_service import BaseSubdomainService

class OtxService(BaseSubdomainService):
    def __init__(self):
        super().__init__()
        self.otx_client = OtxClient(settings.OTX_API_KEY)
        
    def extract_and_store_data(self, db: Session, target_domain):
        data = self.otx_client.get_subdomains(target_domain)
        app_logger.info(f'OTX: fetched {len(data) if data else 0} records for {target_domain}')
        try: 
            if data:
                for block in data:
                    app_logger.debug(f"OTX: processing block={block}")
                    if self.is_valid_subdomain(block["hostname"], target_domain):
                        app_logger.info(f"OTX: valid subdomain found: {block['hostname']}")
                        to_store = {
                            "address": f"{block['address']}",
                            "subdomain": f"{block['hostname']}"
                        }
                        self.store(db, to_store)
                        app_logger.debug(f"OTX: stored {block['hostname']}")
            else:
                app_logger.info(f'no data found for domain {target_domain} in OTX')
                
        except Exception as e:
            app_logger.error(f'error extracting and storing: {e}')
            
    def store(self, db: Session, data: dict):
        # Upsert into service-specific table
        try:
            app_logger.debug(f"OTX: upserting subdomain {data.get('subdomain')}")
            table = OtxSubdomain.__table__
            insert_stmt = pg_insert(table).values(data)
            update_stmt = {k: insert_stmt.excluded[k] for k in data.keys() if k != 'subdomain'}
            if update_stmt:
                stmt = insert_stmt.on_conflict_do_update(index_elements=['subdomain'], set_=update_stmt)
            else:
                stmt = insert_stmt.on_conflict_do_nothing(index_elements=['subdomain'])
            db.execute(stmt)
            db.commit()
            app_logger.info(f"OTX: upserted {data.get('subdomain')} into otx_subdomain")

            # Upsert into master table in Python; merge sources list
            try:
                stmt = select(MasterSubdomains).where(MasterSubdomains.subdomain == data.get('subdomain'))
                master_obj = db.execute(stmt).scalars().one_or_none()
                incoming_first = data.get('detected_at')
                if master_obj is None:
                    master_obj = MasterSubdomains(
                        subdomain=data.get('subdomain'),
                        sources=['otx'],
                        first_seen=incoming_first,
                    )
                    db.add(master_obj)
                else:
                    if 'otx' not in (master_obj.sources or []):
                        master_obj.sources = (master_obj.sources or []) + ['otx']
                    if incoming_first:
                        try:
                            if master_obj.first_seen is None or incoming_first < master_obj.first_seen:
                                master_obj.first_seen = incoming_first
                        except Exception:
                            pass
                    db.add(master_obj)
                db.commit()
                app_logger.info(f"OTX: upserted {data.get('subdomain')} into subdomains_master")
            except Exception as e:
                db.rollback()
                app_logger.error(f"OTX: error upserting into master: {e}")
        except IntegrityError as e:
            db.rollback()
            app_logger.debug(f'error in insert/upsert: {str(e)}')
        except Exception as e:
            db.rollback()
            app_logger.error(f'error upserting otx subdomain: {e}')
        