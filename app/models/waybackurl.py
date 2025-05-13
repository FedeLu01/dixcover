from app.jobs.dixcover import Base
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, relationship

class WaybackUrl(Base):
    __tablename__ = "wayback_urls"
    id = Column(Integer, primary_key=True, index=True)
    url = Column(String, index=True)
    detected_at = Column(DateTime)
    subdomain_id = Column(Integer, ForeignKey("subdomains.id"))
    subdomain = relationship("Subdomain", back_populates="subdomains")