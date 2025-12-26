from typing import List, Optional
from sqlmodel import select
from sqlalchemy import or_, func
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
    def list_master_subdomains(
        db: Session, domain: str, page: Optional[int] = None, per_page: Optional[int] = None
    ) -> List[MasterSubdomains]:
        """List master subdomains for `domain`.

        If `page` and `per_page` are provided, apply OFFSET/LIMIT pagination.
        Results are ordered by `created_at` DESC (newest first) for stable paging.
        """
        pattern = DataConsumeService._like_pattern(domain)
        stmt = (
            select(MasterSubdomains)
            .where(or_(MasterSubdomains.subdomain.ilike(pattern), MasterSubdomains.subdomain == domain))
            .order_by(MasterSubdomains.created_at.desc())
        )

        if page is not None and per_page is not None:
            stmt = stmt.offset(page * per_page).limit(per_page)

        return db.execute(stmt).scalars().all()

    @staticmethod
    def count_master_subdomains(db: Session, domain: str) -> int:
        """Return total number of master subdomains matching `domain`."""
        pattern = DataConsumeService._like_pattern(domain)
        stmt = select(func.count()).select_from(MasterSubdomains).where(
            or_(MasterSubdomains.subdomain.ilike(pattern), MasterSubdomains.subdomain == domain)
        )
        # scalar_one returns the single aggregated integer result
        return int(db.execute(stmt).scalar_one())

    @staticmethod
    def list_alive_subdomains(
        db: Session, domain: str, page: Optional[int] = None, per_page: Optional[int] = None
    ) -> List[AliveSubdomain]:
        """List alive subdomains for `domain`.

        If `page` and `per_page` are provided, apply OFFSET/LIMIT pagination.
        Results are ordered by `probed_at` DESC (most recent probes first).
        """
        pattern = DataConsumeService._like_pattern(domain)
        stmt = (
            select(AliveSubdomain)
            .where(or_(AliveSubdomain.subdomain.ilike(pattern), AliveSubdomain.subdomain == domain))
            .order_by(AliveSubdomain.probed_at.desc())
        )

        if page is not None and per_page is not None:
            stmt = stmt.offset(page * per_page).limit(per_page)

        return db.execute(stmt).scalars().all()

    @staticmethod
    def count_alive_subdomains(db: Session, domain: str) -> int:
        """Return total number of alive subdomains matching `domain`."""
        pattern = DataConsumeService._like_pattern(domain)
        stmt = select(func.count()).select_from(AliveSubdomain).where(
            or_(AliveSubdomain.subdomain.ilike(pattern), AliveSubdomain.subdomain == domain)
        )
        return int(db.execute(stmt).scalar_one())
