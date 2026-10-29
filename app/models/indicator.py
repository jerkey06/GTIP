import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, Text, Integer, Float
from sqlalchemy.dialects.postgresql import UUID
from app.models.base import Base

class Indicator(Base):
    __tablename__ = "indicators"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    value = Column(String(500), unique=True, nullable=False, index=True) # IP, URL o Hash
    type = Column(String(50), nullable=False) # ip, url, domain, md5, sha256
    source_name = Column(String(100), nullable=False) # URLhaus, AbuseIPDB, AlienVault OTX
    threat_type = Column(String(100), nullable=True) # malware, phishing, botnet
    confidence_score = Column(Float, nullable=True)
    description = Column(Text, nullable=True)
    first_seen = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)