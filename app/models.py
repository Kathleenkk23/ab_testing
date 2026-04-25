from sqlalchemy import Column, Integer, String, DateTime, Float
from datetime import datetime
from app.database import Base


class Experiment(Base):
    """A/B Test Experiment model"""
    __tablename__ = "experiments"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    status = Column(String, default="active")  # active, paused, completed


class Assignment(Base):
    """User assignment to experiment variant"""
    __tablename__ = "assignments"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, index=True)
    experiment_id = Column(Integer, index=True)
    variant = Column(String)  # 'control' or 'treatment'
    assigned_at = Column(DateTime, default=datetime.utcnow)


class Event(Base):
    """Track user events (impressions, clicks, conversions)"""
    __tablename__ = "events"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, index=True)
    experiment_id = Column(Integer, index=True)
    variant = Column(String)  # 'control' or 'treatment'
    event_type = Column(String, index=True)  # 'impression', 'click', 'conversion'
    created_at = Column(DateTime, default=datetime.utcnow)
