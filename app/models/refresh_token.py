# app/models/refresh_token.py

from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Index, Integer, String
from sqlalchemy.orm import relationship

from app.db.database import Base


class RefreshToken(Base):
    __tablename__ = "refresh_tokens"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), index=True, nullable=False)
    token = Column(String(512), unique=True, index=True, nullable=False)
    expires_at = Column(DateTime, nullable=False)
    rotated = Column(Boolean, default=False)
    revoked = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    user = relationship("User")

    __table_args__ = (Index("ix_refresh_active", "user_id", "revoked", "rotated"),)
