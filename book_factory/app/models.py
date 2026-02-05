"""SQLAlchemy models for Book Factory."""
from __future__ import annotations

from datetime import datetime

from sqlalchemy import (
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    JSON,
    String,
    Text,
)
from sqlalchemy.orm import relationship

from app.database import Base


class Topic(Base):
    __tablename__ = "topics"

    id = Column(Integer, primary_key=True, autoincrement=True)
    slug = Column(String(255), unique=True, nullable=False, index=True)
    name = Column(String(500), nullable=False)
    series_name = Column(String(500))
    book_title = Column(String(500))
    subtitle = Column(String(500))
    author_voice_preset = Column(String(100), default="default")
    target_audience = Column(Text)
    stance = Column(String(255))
    taboo_list = Column(JSON, default=list)
    keywords = Column(JSON, default=list)
    seed_urls = Column(JSON, default=list)
    draft_target_words = Column(Integer, default=25000)
    final_target_words = Column(Integer, default=30000)
    rrp_usd = Column(Float, default=9.99)
    expected_units = Column(Integer, default=500)
    max_cost_usd = Column(Float, default=15.0)
    status = Column(String(50), default="created")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    published_at = Column(DateTime)

    silos = relationship("Silo", back_populates="topic", cascade="all, delete-orphan")
    author_notes = relationship("AuthorNote", back_populates="topic", cascade="all, delete-orphan")
    sources = relationship("SourceDoc", back_populates="topic", cascade="all, delete-orphan")
    silo_settings = relationship("SiloSetting", back_populates="topic", cascade="all, delete-orphan")


class SiloSetting(Base):
    __tablename__ = "silo_settings"

    id = Column(Integer, primary_key=True, autoincrement=True)
    topic_id = Column(Integer, ForeignKey("topics.id"), nullable=False)
    silo_number = Column(Integer, nullable=False)
    target_words = Column(Integer, default=2000)
    min_sources = Column(Integer, default=5)
    min_nuggets = Column(Integer, default=12)
    template_json = Column(JSON, default=dict)

    topic = relationship("Topic", back_populates="silo_settings")


class Silo(Base):
    __tablename__ = "silos"

    id = Column(Integer, primary_key=True, autoincrement=True)
    topic_id = Column(Integer, ForeignKey("topics.id"), nullable=False)
    silo_number = Column(Integer, nullable=False)
    name_template = Column(String(255), nullable=False)
    custom_title = Column(String(255))
    draft_md_path = Column(Text)
    final_txt_path = Column(Text)
    review_audio_path = Column(Text)
    draft_word_count = Column(Integer, default=0)
    final_word_count = Column(Integer, default=0)
    status = Column(String(50), default="empty")
    sources_count = Column(Integer, default=0)

    topic = relationship("Topic", back_populates="silos")
    notes = relationship("AuthorNote", back_populates="silo", cascade="all, delete-orphan")


class AuthorNote(Base):
    __tablename__ = "author_notes"

    id = Column(Integer, primary_key=True, autoincrement=True)
    topic_id = Column(Integer, ForeignKey("topics.id"), nullable=False)
    silo_id = Column(Integer, ForeignKey("silos.id"), nullable=False)
    text = Column(Text, nullable=False)
    source = Column(String(50), default="telegram")
    created_at = Column(DateTime, default=datetime.utcnow)

    topic = relationship("Topic", back_populates="author_notes")
    silo = relationship("Silo", back_populates="notes")


class TrendCandidate(Base):
    __tablename__ = "trend_candidates"

    id = Column(Integer, primary_key=True, autoincrement=True)
    source = Column(String(50), default="rss")
    topic_name = Column(String(500), nullable=False)
    description = Column(Text)
    trend_score = Column(Float)
    discovered_at = Column(DateTime, default=datetime.utcnow)
    status = Column(String(50), default="new")


class SourceDoc(Base):
    __tablename__ = "source_docs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    topic_id = Column(Integer, ForeignKey("topics.id"), nullable=False)
    url = Column(Text, nullable=False)
    title = Column(String(500))
    domain = Column(String(255))
    doc_type = Column(String(50), default="url")
    status = Column(String(50), default="pending")
    source = Column(String(50), default="manual")
    created_at = Column(DateTime, default=datetime.utcnow)

    topic = relationship("Topic", back_populates="sources")
