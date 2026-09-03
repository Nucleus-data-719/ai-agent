from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import Optional
import os
import uuid
from datetime import datetime
from dotenv import load_dotenv
from sqlalchemy.orm import Session

# Load environment
load_dotenv()

print("=" * 60)
print("🚀 Starting Lead Agent API")
print("=" * 60)
print(f"🔑 API Key: {'✅ Loaded' if os.getenv('OPENAI_API_KEY') else '❌ Not found'}")
print(f"📦 Model: {os.getenv('OPENAI_MODEL', 'gpt-4o-mini')}")
print(f"💾 Database: {'✅ Connected' if os.getenv('DATABASE_URL') else '⚠️ Using memory (no DB)'}")
print("=" * 60)

from .agent import LeadAgent
from .scoring import calculate_lead_score, get_lead_summary
from .models import init_db, get_db
from .database import save_conversation, save_lead, get_all_leads, get_lead_by_id, get_lead_stats

# Initialize database
init_db()

# Initialize app and agent
app = FastAPI(title="Lead Agent API", version="1.0.0")
agent = LeadAgent()

# Allow CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Models ---
class ChatRequest(BaseModel):
    message: str
    conversation_id: Optional[str] = None

class ChatResponse(BaseModel):
    response: str
    conversation_id: str
    lead_data: Optional[dict] = None
    lead_score: Optional[int] = None
    lead_priority: Optional[str] = None
    lead_summary: Optional[dict] = None

class LeadStatusUpdate(BaseModel):
    status: str  # new, contacted, converted, lost
    notes: Optional[str] = None

# --- In-memory fallback (if no DB) ---
conversations = {}
leads = {}

# --- Endpoints ---
@app.get("/")
async def root():
    widget_path = os.path.join(os.path.dirname(__file__), "frontend", "widget.html")
    if os.path.exists(widget_path):
        return FileResponse(widget_path)
    return {"message": "Lead Agent API is running!"}

@app.get("/health")
async def health():
    return {"status": "healthy", "database": "connected" if os.getenv("DATABASE_URL") else "memory"}

@app.get("/chat/test")
async def chat_test():
    return {
        "status": "ok",
        "message": "Chat endpoint works! Use POST to send messages.",
        "example": {
            "method": "POST",
            "body": {
                "message": "I want a 5 marla house in DHA",
                "conversation_id": "optional-uuid"
            }
        }
    }

@app.get("/leads")
async def get_all_leads_endpoint(db: Session = Depends(get_db)):
    """Get all leads with their scores"""
    if os.getenv("DATABASE_URL"):
        leads = get_all_leads(db)
        return {
            "total": len(leads),
            "leads": [{
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
                "created_at": lead.created_at.isoformat() if lead.created_at else None,
                "updated_at": lead.updated_at.isoformat() if lead.updated_at else None
            } for lead in leads]
        }
    else:
        # Fallback to memory
        return {
            "total": len(leads),
            "leads": leads
        }

@app.get("/leads/stats")
async def get_stats(db: Session = Depends(get_db)):
    """Get lead statistics"""
    if os.getenv("DATABASE_URL"):
        return get_lead_stats(db)
    else:
        # Fallback to memory
        total = len(leads)
        hot = sum(1 for l in leads.values() if l.get('score', {}).get('priority') == 'HOT')
        warm = sum(1 for l in leads.values() if l.get('score', {}).get('priority') == 'WARM')
        cold = sum(1 for l in leads.values() if l.get('score', {}).get('priority') == 'COLD')
        low = sum(1 for l in leads.values() if l.get('score', {}).get('priority') == 'LOW')
        return {"total": total, "hot": hot, "warm": warm, "cold": cold, "low": low}

@app.get("/leads/{conversation_id}")
async def get_lead(conversation_id: str, db: Session = Depends(get_db)):
    """Get a specific lead by conversation ID"""
    if os.getenv("DATABASE_URL"):
        lead = get_lead_by_id(db, conversation_id)
        if not lead:
            raise HTTPException(status_code=404, detail="Lead not found")
        return lead
    else:
        # Fallback to memory
        if conversation_id not in leads:
            raise HTTPException(status_code=404, detail="Lead not found")
        return leads[conversation_id]

@app.put("/leads/{conversation_id}/status")
async def update_lead_status(
    conversation_id: str,
    update: LeadStatusUpdate,
    db: Session = Depends(get_db)
):
    """Update lead status"""
    from .database import update_lead_status
    lead = update_lead_status(db, conversation_id, update.status, update.notes)
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    return {"status": "updated", "lead": {
        "id": lead.id,
        "status": lead.status,
        "notes": lead.notes
    }}

@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest, db: Session = Depends(get_db)):
    """
    Main chat endpoint for lead qualification
    """
    # Generate or use existing conversation ID
    conversation_id = request.conversation_id or str(uuid.uuid4())
    
    # Initialize conversation if new
    if conversation_id not in conversations:
        conversations[conversation_id] = []
    
    # Add user message to history
    conversations[conversation_id].append({
        "role": "user",
        "content": request.message,
        "timestamp": datetime.now().isoformat()
    })
    
    # Get AI response
    ai_response = await agent.get_response(conversations[conversation_id])
    
    # Add AI response to history
    conversations[conversation_id].append({
        "role": "assistant",
        "content": ai_response,
        "timestamp": datetime.now().isoformat()
    })
    
    # Save conversation to database (if available)
    if os.getenv("DATABASE_URL"):
        save_conversation(db, conversation_id, conversations[conversation_id])
    
    # Extract lead data from entire conversation
    lead_data = agent.extract_lead_data(conversations[conversation_id])
    
    # Calculate lead score
    score_result = calculate_lead_score(lead_data)
    lead_summary = get_lead_summary(lead_data, score_result)
    
    # Save lead to database (if available)
    if os.getenv("DATABASE_URL"):
        save_lead(db, conversation_id, lead_data, score_result, lead_summary)
    
    # Also save to memory (for fallback)
    leads[conversation_id] = {
        "conversation_id": conversation_id,
        "data": lead_data,
        "score": score_result,
        "summary": lead_summary,
        "conversation": conversations[conversation_id],
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat()
    }
    
    # Print lead summary to console (for demo purposes)
    print("\n" + "=" * 60)
    print(f"📊 NEW LEAD: {lead_summary['title']}")
    print("=" * 60)
    print(f"Score: {lead_summary['score']}")
    for detail in lead_summary['details']:
        print(f"  • {detail}")
    print("\n✅ Positive signals:")
    for reason in lead_summary['reasons']:
        print(f"  {reason}")
    if lead_summary['missing']:
        print("\n⚠️ Missing information:")
        for item in lead_summary['missing']:
            print(f"  • {item}")
    print("=" * 60 + "\n")
    
    return ChatResponse(
        response=ai_response,
        conversation_id=conversation_id,
        lead_data=lead_data,
        lead_score=score_result["score"],
        lead_priority=score_result["priority"],
        lead_summary=lead_summary
    )