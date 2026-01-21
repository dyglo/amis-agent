from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, JSON, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from amis_agent.infrastructure.db.base import Base


class CompanyModel(Base):
    __tablename__ = "companies"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    industry: Mapped[Optional[str]] = mapped_column(String(255))
    region: Mapped[Optional[str]] = mapped_column(String(16))
    website_status: Mapped[Optional[str]] = mapped_column(String(64))
    website_url: Mapped[Optional[str]] = mapped_column(String(512))
    website_domain: Mapped[Optional[str]] = mapped_column(String(255), index=True)
    about_snippet: Mapped[Optional[str]] = mapped_column(String(512))
    source: Mapped[Optional[str]] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    leads: Mapped[list["LeadModel"]] = relationship(back_populates="company")
    contacts: Mapped[list["ContactModel"]] = relationship(back_populates="company")
    qualification: Mapped[Optional["CompanyQualificationModel"]] = relationship(back_populates="company")


class LeadModel(Base):
    __tablename__ = "leads"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    company_id: Mapped[int] = mapped_column(ForeignKey("companies.id"), nullable=False, index=True)
    contact_name: Mapped[Optional[str]] = mapped_column(String(255))
    contact_role: Mapped[Optional[str]] = mapped_column(String(255))
    contact_email: Mapped[Optional[str]] = mapped_column(String(255), index=True)
    contact_status: Mapped[str] = mapped_column(String(32), nullable=False, default="pending")
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="new")
    region: Mapped[Optional[str]] = mapped_column(String(16))
    verification_status: Mapped[Optional[str]] = mapped_column(String(64))
    opt_in: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    contact_id: Mapped[Optional[int]] = mapped_column(ForeignKey("contacts.id"), index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    company: Mapped[CompanyModel] = relationship(back_populates="leads")
    contact: Mapped[Optional["ContactModel"]] = relationship(back_populates="leads")
    outreach: Mapped[list["OutreachModel"]] = relationship(back_populates="lead")
    outbox: Mapped[list["OutboxModel"]] = relationship(back_populates="lead")


class OutreachModel(Base):
    __tablename__ = "outreach"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    lead_id: Mapped[int] = mapped_column(ForeignKey("leads.id"), nullable=False, index=True)
    template_id: Mapped[Optional[str]] = mapped_column(String(64))
    subject: Mapped[str] = mapped_column(String(255), nullable=False)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    language: Mapped[Optional[str]] = mapped_column(String(32))
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="queued")
    sent_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    lead: Mapped[LeadModel] = relationship(back_populates="outreach")
    replies: Mapped[list["ReplyModel"]] = relationship(back_populates="outreach")


class ReplyModel(Base):
    __tablename__ = "replies"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    outreach_id: Mapped[int] = mapped_column(ForeignKey("outreach.id"), nullable=False, index=True)
    sentiment: Mapped[Optional[str]] = mapped_column(String(32))
    reply_text: Mapped[Optional[str]] = mapped_column(Text)
    classification: Mapped[Optional[str]] = mapped_column(String(64))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    outreach: Mapped[OutreachModel] = relationship(back_populates="replies")


class SuppressionModel(Base):
    __tablename__ = "suppression"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    email: Mapped[str] = mapped_column(String(255), nullable=False, unique=True, index=True)
    reason: Mapped[Optional[str]] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class AuditLogModel(Base):
    __tablename__ = "audit_log"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    action: Mapped[str] = mapped_column(String(128), nullable=False)
    source: Mapped[Optional[str]] = mapped_column(String(255))
    legal_basis: Mapped[Optional[str]] = mapped_column(String(255))
    details: Mapped[Optional[str]] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class CompanyQualificationModel(Base):
    __tablename__ = "company_qualification"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    company_id: Mapped[int] = mapped_column(ForeignKey("companies.id"), nullable=False, unique=True, index=True)
    decision: Mapped[str] = mapped_column(String(32), nullable=False)
    score: Mapped[int] = mapped_column(Integer, nullable=False)
    reason: Mapped[Optional[str]] = mapped_column(Text)
    decided_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    company: Mapped[CompanyModel] = relationship(back_populates="qualification")


class ContactModel(Base):
    __tablename__ = "contacts"
    __table_args__ = (UniqueConstraint("company_id", "email", name="uq_contacts_company_email"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    company_id: Mapped[int] = mapped_column(ForeignKey("companies.id"), nullable=False, index=True)
    email: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    source_url: Mapped[Optional[str]] = mapped_column(String(512))
    confidence: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    discovered_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    company: Mapped[CompanyModel] = relationship(back_populates="contacts")
    leads: Mapped[list["LeadModel"]] = relationship(back_populates="contact")


class OutboxModel(Base):
    __tablename__ = "outbox"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    lead_id: Mapped[int] = mapped_column(ForeignKey("leads.id"), nullable=False, index=True)
    to_email: Mapped[Optional[str]] = mapped_column(String(255), index=True)
    subject: Mapped[str] = mapped_column(String(255), nullable=False)
    subject_variants: Mapped[Optional[list]] = mapped_column(JSON)
    body_text: Mapped[str] = mapped_column(Text, nullable=False)
    body_html: Mapped[Optional[str]] = mapped_column(Text)
    followup_text: Mapped[Optional[str]] = mapped_column(Text)
    personalization_vars: Mapped[Optional[dict]] = mapped_column(JSON)
    personalization_fact: Mapped[Optional[str]] = mapped_column(Text)
    personalization_source_url: Mapped[Optional[str]] = mapped_column(String(512))
    prompt_hash: Mapped[Optional[str]] = mapped_column(String(64), index=True)
    llm_model: Mapped[Optional[str]] = mapped_column(String(128))
    llm_latency_ms: Mapped[Optional[int]] = mapped_column(Integer)
    llm_token_usage: Mapped[Optional[dict]] = mapped_column(JSON)
    llm_confidence: Mapped[Optional[float]] = mapped_column(Float)
    llm_rationale: Mapped[Optional[str]] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="draft")
    approved_by_human: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    approved_by: Mapped[Optional[str]] = mapped_column(String(255))
    approved_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    lead: Mapped[LeadModel] = relationship(back_populates="outbox")


class IndustryInsightModel(Base):
    __tablename__ = "industry_insights"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    industry: Mapped[str] = mapped_column(String(255), nullable=False, unique=True, index=True)
    preferred_persona: Mapped[Optional[str]] = mapped_column(String(64))
    preferred_subject_variant: Mapped[Optional[int]] = mapped_column(Integer)
    notes: Mapped[Optional[str]] = mapped_column(Text)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class ReplyPatternModel(Base):
    __tablename__ = "reply_patterns"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    pattern_text: Mapped[str] = mapped_column(String(255), nullable=False, unique=True, index=True)
    classification: Mapped[Optional[str]] = mapped_column(String(64))
    occurrences: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    last_seen_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

