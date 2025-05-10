from app.database import Base
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, relationship

class Subdomain(Base):
    __tablename__ = "subdomains"
    id = Column(Integer, primary_key=True, index=True)
    subdomain = Column(String, index=True)
    detected_at = Column(DateTime)
    subdomain_id = Column(Integer, ForeignKey("subdomains.id"))
    wayback_url = relationship("WaybackUrl", back_populates="wayback_url")
    