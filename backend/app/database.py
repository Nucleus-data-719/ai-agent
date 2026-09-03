from sqlalchemy.orm import Session
from datetime import datetime
from .models import Conversation, Lead, get_db
import json

def save_conversation(db: Session, conversation_id: str, messages: list):
    """Save or update a conversation"""
    conv = db.query(Conversation).filter(Conversation.id == conversation_id).first()
    
    if conv:
        conv.messages = messages
        conv.updated_at = datetime.utcnow()
    else:
        conv = Conversation(
            id=conversation_id,
            messages=messages,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        db.add(conv)
    
    db.commit()
    return conv

def save_lead(db: Session, conversation_id: str, lead_data: dict, score_result: dict, summary: dict):
    """Save or update a lead"""
    
    # Update conversation with lead data
    conv = db.query(Conversation).filter(Conversation.id == conversation_id).first()
    if conv:
        conv.lead_data = lead_data
        conv.score = score_result.get("score", 0)
        conv.priority = score_result.get("priority", "LOW")
        conv.score_reasons = score_result.get("reasons", [])
        conv.score_missing = score_result.get("missing", [])
        conv.summary = summary
        conv.updated_at = datetime.utcnow()
    
    # Create or update lead record
    lead = db.query(Lead).filter(Lead.id == conversation_id).first()
    
    if lead:
        # Update existing lead
        lead.name = lead_data.get("name")
        lead.phone = lead_data.get("phone")
        lead.email = lead_data.get("email")
        lead.property_type = lead_data.get("property_type")
        lead.location = lead_data.get("location")
        lead.size = lead_data.get("size")
        lead.budget = lead_data.get("budget")
        lead.timeline = lead_data.get("timeline")
        lead.purpose = lead_data.get("purpose")
        lead.bedrooms = lead_data.get("bedrooms")
        lead.score = score_result.get("score", 0)
        lead.priority = score_result.get("priority", "LOW")
        lead.updated_at = datetime.utcnow()
    else:
        # Create new lead
        lead = Lead(
            id=conversation_id,
            name=lead_data.get("name"),
            phone=lead_data.get("phone"),
            email=lead_data.get("email"),
            property_type=lead_data.get("property_type"),
            location=lead_data.get("location"),
            size=lead_data.get("size"),
            budget=lead_data.get("budget"),
            timeline=lead_data.get("timeline"),
            purpose=lead_data.get("purpose"),
            bedrooms=lead_data.get("bedrooms"),
            score=score_result.get("score", 0),
            priority=score_result.get("priority", "LOW"),
            conversation_id=conversation_id,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        db.add(lead)
    
    db.commit()
    return lead

def get_all_leads(db: Session):
    """Get all leads with their scores"""
    leads = db.query(Lead).order_by(Lead.score.desc()).all()
    return leads

def get_lead_by_id(db: Session, conversation_id: str):
    """Get a specific lead by conversation ID"""
    lead = db.query(Lead).filter(Lead.id == conversation_id).first()
    if not lead:
        return None
    
    # Get conversation
    conv = db.query(Conversation).filter(Conversation.id == conversation_id).first()
    
    return {
        "conversation_id": lead.id,
        "data": {
            "name": lead.name,
            "phone": lead.phone,
            "email": lead.email,
            "property_type": lead.property_type,
            "location": lead.location,
            "size": lead.size,
            "budget": lead.budget,
            "timeline": lead.timeline,
            "purpose": lead.purpose,
            "bedrooms": lead.bedrooms
        },
        "score": {
            "score": lead.score,
            "priority": lead.priority,
            "reasons": lead.score_reasons if hasattr(lead, 'score_reasons') else [],
            "missing": lead.score_missing if hasattr(lead, 'score_missing') else []
        },
        "conversation": conv.messages if conv else [],
        "created_at": lead.created_at.isoformat() if lead.created_at else None,
        "updated_at": lead.updated_at.isoformat() if lead.updated_at else None
    }

def get_lead_stats(db: Session):
    """Get lead statistics"""
    total = db.query(Lead).count()
    hot = db.query(Lead).filter(Lead.priority == "HOT").count()
    warm = db.query(Lead).filter(Lead.priority == "WARM").count()
    cold = db.query(Lead).filter(Lead.priority == "COLD").count()
    low = db.query(Lead).filter(Lead.priority == "LOW").count()
    
    return {
        "total": total,
        "hot": hot,
        "warm": warm,
        "cold": cold,
        "low": low
    }

def update_lead_status(db: Session, conversation_id: str, status: str, notes: str = None):
    """Update lead status (new, contacted, converted, lost)"""
    lead = db.query(Lead).filter(Lead.id == conversation_id).first()
    if lead:
        lead.status = status
        if notes:
            lead.notes = notes
        lead.updated_at = datetime.utcnow()
        db.commit()
        return lead
    return None