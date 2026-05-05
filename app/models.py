from sqlalchemy import Column, Integer, String, DateTime, Float, Text, ForeignKey
from datetime import datetime
from app.database import Base


class Experiment(Base):
    """A/B Test Experiment model"""
    __tablename__ = "experiments"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    status = Column(String, default="active")  # active, paused, completed


class Creative(Base):
    """Creative asset for experiments (images, copy, designs)"""
    __tablename__ = "creatives"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    description = Column(Text)
    creative_type = Column(String, index=True)  # 'image', 'copy', 'video', 'design'
    content = Column(Text)  # URL, HTML, or content
    creative_metadata = Column(Text)  # JSON string with additional properties
    created_at = Column(DateTime, default=datetime.utcnow)


class CreativeVariant(Base):
    """Links creatives to experiment variants"""
    __tablename__ = "creative_variants"

    id = Column(Integer, primary_key=True, index=True)
    experiment_id = Column(Integer, ForeignKey("experiments.id"), index=True)
    variant = Column(String)  # 'control' or 'treatment'
    creative_id = Column(Integer, ForeignKey("creatives.id"), index=True)
    created_at = Column(DateTime, default=datetime.utcnow)


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
    creative_id = Column(Integer, ForeignKey("creatives.id"), nullable=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
