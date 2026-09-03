from sqlalchemy import create_engine, Column, String, Integer, Float, DateTime, JSON, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
import os

# Database setup
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./lead_agent.db")

print(f"💾 Database URL: {DATABASE_URL[:50]}..." if len(DATABASE_URL) > 50 else f"💾 Database URL: {DATABASE_URL}")

# Handle different database types
if DATABASE_URL.startswith("sqlite"):
    print("   Using SQLite (development mode)")
    engine = create_engine(
        DATABASE_URL, 
        connect_args={"check_same_thread": False}
    )
else:
    print("   Using PostgreSQL (production mode)")
    # Neon works with standard PostgreSQL settings
    engine = create_engine(DATABASE_URL)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Database Models
class Conversation(Base):
    __tablename__ = "conversations"
    
    id = Column(String, primary_key=True)  # conversation_id
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    messages = Column(JSON, default=[])  # Store all messages
    lead_data = Column(JSON, default={})  # Extracted lead data
    score = Column(Integer, default=0)
    priority = Column(String, default="LOW")
    score_reasons = Column(JSON, default=[])  # List of reasons
    score_missing = Column(JSON, default=[])  # Missing fields
    summary = Column(JSON, default={})  # Full summary
    status = Column(String, default="active")  # active, converted, lost

class Lead(Base):
    __tablename__ = "leads"
    
    id = Column(String, primary_key=True)  # Same as conversation_id
    name = Column(String, nullable=True)
    phone = Column(String, nullable=True)
    email = Column(String, nullable=True)
    property_type = Column(String, nullable=True)
    location = Column(String, nullable=True)
    size = Column(String, nullable=True)
    budget = Column(String, nullable=True)
    timeline = Column(String, nullable=True)
    purpose = Column(String, nullable=True)
    bedrooms = Column(String, nullable=True)
    score = Column(Integer, default=0)
    priority = Column(String, default="LOW")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    conversation_id = Column(String, nullable=True)  # Link to conversation
    status = Column(String, default="new")  # new, contacted, converted, lost
    notes = Column(Text, nullable=True)

# Create tables
def init_db():
    """Initialize database tables"""
    Base.metadata.create_all(bind=engine)
    print("✅ Database tables created/verified")

# Dependency to get DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()