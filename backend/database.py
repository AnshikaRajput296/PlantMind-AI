"""
Structured persistence layer.

Uses SQLite via SQLAlchemy for the hackathon build so the platform runs
with zero external services. Swap the URL below for a PostgreSQL DSN in
production (`postgresql+psycopg2://user:pass@host/db`) -- no other code
needs to change because the app only talks to the ORM layer.
"""
from __future__ import annotations

import datetime as dt
from sqlalchemy import (
    create_engine, Column, Integer, String, Float, DateTime, Text, ForeignKey
)
from sqlalchemy.orm import declarative_base, sessionmaker, relationship

from backend.config import DB_PATH

engine = create_engine(f"sqlite:///{DB_PATH}", connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
Base = declarative_base()


class Document(Base):
    __tablename__ = "documents"
    id = Column(Integer, primary_key=True)
    filename = Column(String, nullable=False)
    doc_type = Column(String)               # pdf / docx / xlsx / csv / image / txt
    category = Column(String)               # maintenance / inspection / sop / compliance ...
    uploaded_at = Column(DateTime, default=dt.datetime.utcnow)
    raw_text_path = Column(String)
    summary = Column(Text)
    entity_json = Column(Text)              # extracted entities, serialized JSON


class Chunk(Base):
    __tablename__ = "chunks"
    id = Column(Integer, primary_key=True)
    document_id = Column(Integer, ForeignKey("documents.id"))
    chunk_index = Column(Integer)
    text = Column(Text)
    parent_text = Column(Text)              # parent chunk for parent-child retrieval
    document = relationship("Document")


class Equipment(Base):
    __tablename__ = "equipment"
    id = Column(Integer, primary_key=True)
    tag = Column(String, unique=True)       # e.g. P-101
    name = Column(String)
    plant = Column(String)
    manufacturer = Column(String)
    install_date = Column(String)
    risk_score = Column(Float, default=0.0)
    rul_days = Column(Float, default=0.0)   # remaining useful life estimate


class WorkOrder(Base):
    __tablename__ = "work_orders"
    id = Column(Integer, primary_key=True)
    equipment_tag = Column(String)
    date = Column(String)
    technician = Column(String)
    description = Column(Text)
    failure_mode = Column(String)
    downtime_hours = Column(Float, default=0.0)
    cost = Column(Float, default=0.0)
    document_id = Column(Integer, ForeignKey("documents.id"), nullable=True)


class Incident(Base):
    __tablename__ = "incidents"
    id = Column(Integer, primary_key=True)
    equipment_tag = Column(String)
    date = Column(String)
    department = Column(String)
    severity = Column(String)
    description = Column(Text)
    regulation_ref = Column(String)


class AuditLog(Base):
    __tablename__ = "audit_log"
    id = Column(Integer, primary_key=True)
    ts = Column(DateTime, default=dt.datetime.utcnow)
    user = Column(String)
    action = Column(String)
    detail = Column(Text)


def init_db():
    Base.metadata.create_all(engine)


def get_session():
    return SessionLocal()
