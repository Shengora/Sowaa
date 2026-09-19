import enum
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Enum, Text, JSON
from sqlalchemy.orm import relationship
from datetime import datetime
from bot.database.core import Base

class Role(str, enum.Enum):
    admin = "admin"
    lawyer = "lawyer"
    client = "client"

class CaseStatus(str, enum.Enum):
    new = "new"
    in_progress = "in_progress"
    waiting_documents = "waiting_documents"
    submitted = "submitted"
    completed = "completed"

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    telegram_id = Column(Integer, unique=True, index=True, nullable=False)
    role = Column(Enum(Role), nullable=False)
    language = Column(String, default="uz", nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

class Lawyer(Base):
    __tablename__ = "lawyers"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False)
    invite_token = Column(String, unique=True, index=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User")
    clients = relationship("Client", back_populates="lawyer")
    cases = relationship("Case", back_populates="lawyer")
    templates = relationship("DocumentTemplate", back_populates="lawyer")

class Client(Base):
    __tablename__ = "clients"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False)
    lawyer_id = Column(Integer, ForeignKey("lawyers.id"), nullable=False)
    encrypted_passport = Column(String, nullable=True)
    encrypted_address = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User")
    lawyer = relationship("Lawyer", back_populates="clients")
    cases = relationship("Case", back_populates="client")

class Case(Base):
    __tablename__ = "cases"
    id = Column(Integer, primary_key=True, index=True)
    client_id = Column(Integer, ForeignKey("clients.id"), nullable=False)
    lawyer_id = Column(Integer, ForeignKey("lawyers.id"), nullable=False)
    title = Column(String, nullable=False)
    status = Column(Enum(CaseStatus), default=CaseStatus.new, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    client = relationship("Client", back_populates="cases")
    lawyer = relationship("Lawyer", back_populates="cases")
    history = relationship("CaseStatusHistory", back_populates="case_ref")

class CaseStatusHistory(Base):
    __tablename__ = "case_status_history"
    id = Column(Integer, primary_key=True, index=True)
    case_id = Column(Integer, ForeignKey("cases.id"), nullable=False)
    status = Column(Enum(CaseStatus), nullable=False)
    note = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    case_ref = relationship("Case", back_populates="history")

class DocumentTemplate(Base):
    __tablename__ = "document_templates"
    id = Column(Integer, primary_key=True, index=True)
    lawyer_id = Column(Integer, ForeignKey("lawyers.id"), nullable=False)
    name = Column(String, nullable=False)
    file_path = Column(String, nullable=False)
    questions = Column(JSON, nullable=False) # list of dicts with key, question, type, required, validation
    created_at = Column(DateTime, default=datetime.utcnow)

    lawyer = relationship("Lawyer", back_populates="templates")

class GeneratedDocument(Base):
    __tablename__ = "generated_documents"
    id = Column(Integer, primary_key=True, index=True)
    template_id = Column(Integer, ForeignKey("document_templates.id"), nullable=False)
    client_id = Column(Integer, ForeignKey("clients.id"), nullable=False)
    file_path = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

class Subscription(Base):
    __tablename__ = "subscriptions"
    id = Column(Integer, primary_key=True, index=True)
    lawyer_id = Column(Integer, ForeignKey("lawyers.id"), nullable=False)
    plan_name = Column(String, nullable=False, default="trial")
    active_until = Column(DateTime, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

class AuditLog(Base):
    __tablename__ = "audit_logs"
    id = Column(Integer, primary_key=True, index=True)
    lawyer_id = Column(Integer, ForeignKey("lawyers.id"), nullable=True)
    actor_telegram_id = Column(Integer, nullable=False)
    action = Column(String, nullable=False)
    target_type = Column(String, nullable=False)
    target_id = Column(Integer, nullable=False)
    details = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)