from typing import List
from sqlmodel import select
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.models.subdomains_master import MasterSubdomains
from app.models.alive_subdomain import AliveSubdomain


class DataConsumeService:
    """Service encapsulating DB queries for the data-consume endpoint.

    Keeps ORM access out of the controller and centralizes pagination and
    filtering logic so it's easier to test and reuse.
    """

    @staticmethod
    def _like_pattern(domain: str) -> str:
        return f"%.{domain}"

    @staticmethod
    def list_master_subdomains(db: Session, domain: str, page: int, per_page: int) -> List[MasterSubdomains]:
        pattern = DataConsumeService._like_pattern(domain)
        stmt = (
            select(MasterSubdomains)
            .where(or_(MasterSubdomains.subdomain.ilike(pattern), MasterSubdomains.subdomain == domain))
            .offset(page * per_page)
            .limit(per_page)
        )
        # Use SQLAlchemy-compatible execute() and scalars() to retrieve ORM objects
        return db.execute(stmt).scalars().all()

    @staticmethod
    def list_all_master_subdomains(db: Session, domain: str) -> List[MasterSubdomains]:
        pattern = DataConsumeService._like_pattern(domain)
        stmt = (
            select(MasterSubdomains)
            .where(or_(MasterSubdomains.subdomain.ilike(pattern), MasterSubdomains.subdomain == domain))
        )
        return db.execute(stmt).scalars().all()

    @staticmethod
    def list_alive_subdomains(db: Session, domain: str, page: int, per_page: int) -> List[AliveSubdomain]:
        pattern = DataConsumeService._like_pattern(domain)
        stmt = (
            select(AliveSubdomain)
            .where(or_(AliveSubdomain.subdomain.ilike(pattern), AliveSubdomain.subdomain == domain))
            .offset(page * per_page)
            .limit(per_page)
        )
        # Use SQLAlchemy-compatible execute() and scalars() to retrieve ORM objects
        return db.execute(stmt).scalars().all()

    @staticmethod
    def list_all_alive_subdomains(db: Session, domain: str) -> List[AliveSubdomain]:
        pattern = DataConsumeService._like_pattern(domain)
        stmt = (
            select(AliveSubdomain)
            .where(or_(AliveSubdomain.subdomain.ilike(pattern), AliveSubdomain.subdomain == domain))
        )
        return db.execute(stmt).scalars().all()
