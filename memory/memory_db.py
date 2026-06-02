import os
import uuid
from datetime import datetime
from contextlib import contextmanager
from sqlalchemy import create_engine, Column, String, Text, Float, Integer, DateTime, JSON, Enum as SAEnum, ForeignKey
from sqlalchemy.orm import declarative_base, relationship, sessionmaker, Session
from dotenv import load_dotenv
from loguru import logger
import enum

Base = declarative_base()

class FactType(str, enum.Enum):
    INTEREST = 'interest'
    PROJECT = 'project'
    GOAL = 'goal'
    QUESTION = 'question'
    BELIEF = 'belief'
    BACKGROUND = 'background'

class User(Base):
    __tablename__ = 'users'
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    username = Column(String, unique=True, nullable=False)
    display_name = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_active = Column(DateTime, default=datetime.utcnow)
    
    conversations = relationship('Conversation', back_populates='user')
    facts = relationship('UserFact', back_populates='user')

class Conversation(Base):
    __tablename__ = 'conversations'
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey('users.id'), nullable=False)
    session_id = Column(String, nullable=False)
    started_at = Column(DateTime, default=datetime.utcnow)
    last_turn_at = Column(DateTime, default=datetime.utcnow)
    summary_text = Column(Text, nullable=True)
    turn_count = Column(Integer, default=0)
    
    user = relationship('User', back_populates='conversations')
    turns = relationship('ConversationTurn', back_populates='conversation', order_by='ConversationTurn.timestamp')

class ConversationTurn(Base):
    __tablename__ = 'conversation_turns'
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    conversation_id = Column(String, ForeignKey('conversations.id'), nullable=False)
    role = Column(String, nullable=False) # 'user' or 'assistant'
    content = Column(Text, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)
    intent_detected = Column(String, nullable=True)
    topics_json = Column(JSON, nullable=True)
    timeline_year = Column(Integer, nullable=True)
    
    conversation = relationship('Conversation', back_populates='turns')
    facts_extracted = relationship('UserFact', back_populates='source_turn')

class UserFact(Base):
    __tablename__ = 'user_facts'
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey('users.id'), nullable=False)
    fact_type = Column(SAEnum(FactType), nullable=False)
    fact_text = Column(Text, nullable=False)
    confidence = Column(Float, default=1.0)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_confirmed = Column(DateTime, default=datetime.utcnow, nullable=True)
    source_turn_id = Column(String, ForeignKey('conversation_turns.id'), nullable=True)
    
    user = relationship('User', back_populates='facts')
    source_turn = relationship('ConversationTurn', back_populates='facts_extracted')

class MemoryDatabase:
    def __init__(self, db_path: str = None):
        load_dotenv()
        db_path = db_path or os.getenv('SQLITE_DB_PATH', './memory.db')
        
        # Support both raw file paths and full SQLAlchemy URLs
        if db_path.startswith('sqlite'):
            # Already a full SQLAlchemy URL (e.g. sqlite:///:memory: or sqlite:///path/to/db)
            db_url = db_path
        else:
            # Raw file path — ensure directory exists, then prefix
            db_dir = os.path.dirname(db_path)
            if db_dir and not os.path.exists(db_dir):
                os.makedirs(db_dir)
            db_url = f'sqlite:///{db_path}'
            
        self.engine = create_engine(db_url, echo=False)
        Base.metadata.create_all(self.engine)
        self.SessionLocal = sessionmaker(bind=self.engine)
        logger.info(f"Memory database initialized at {db_url}")
    
    @contextmanager
    def get_session(self) -> Session:
        session = self.SessionLocal()
        try:
            yield session
            session.commit()
        except Exception as e:
            session.rollback()
            logger.error(f"Database error: {e}")
            raise
        finally:
            session.close()
    
    def create_user(self, username: str, display_name: str = None) -> dict:
        with self.get_session() as session:
            user = session.query(User).filter(User.username == username).first()
            if not user:
                user = User(username=username, display_name=display_name or username)
                session.add(user)
                session.commit()
            return {"id": user.id, "username": user.username, "display_name": user.display_name}
            
    def get_user(self, username: str) -> dict | None:
        with self.get_session() as session:
            user = session.query(User).filter(User.username == username).first()
            if user:
                return {"id": user.id, "username": user.username, "display_name": user.display_name}
            return None
            
    def start_conversation(self, user_id: str) -> dict:
        with self.get_session() as session:
            conv = Conversation(
                user_id=user_id,
                session_id=str(uuid.uuid4())
            )
            session.add(conv)
            session.commit()
            return {"id": conv.id, "session_id": conv.session_id, "user_id": conv.user_id}
            
    def add_turn(self, conversation_id: str, role: str, content: str, 
                 intent: str = None, topics: list = None, timeline_year: int = None) -> dict:
        with self.get_session() as session:
            turn = ConversationTurn(
                conversation_id=conversation_id,
                role=role,
                content=content,
                intent_detected=intent,
                topics_json=topics or [],
                timeline_year=timeline_year
            )
            session.add(turn)
            
            # Update conversation metadata
            conv = session.query(Conversation).filter(Conversation.id == conversation_id).first()
            if conv:
                conv.last_turn_at = datetime.utcnow()
                conv.turn_count += 1
                
                # Update user last active
                user = session.query(User).filter(User.id == conv.user_id).first()
                if user:
                    user.last_active = datetime.utcnow()
                    
            session.commit()
            return {"id": turn.id, "conversation_id": turn.conversation_id, "role": turn.role}
            
    def get_recent_turns(self, conversation_id: str, n: int = 10) -> list[dict]:
        with self.get_session() as session:
            turns = session.query(ConversationTurn).filter(
                ConversationTurn.conversation_id == conversation_id
            ).order_by(ConversationTurn.timestamp.desc()).limit(n).all()
            
            # Return in chronological order
            return [{"role": t.role, "content": t.content} for t in reversed(turns)]
            
    def save_fact(self, user_id: str, fact_type: str, fact_text: str, 
                  confidence: float, source_turn_id: str = None) -> dict:
        with self.get_session() as session:
            # Simple deduplication - check if identical fact text exists
            existing = session.query(UserFact).filter(
                UserFact.user_id == user_id,
                UserFact.fact_text == fact_text
            ).first()
            
            if existing:
                existing.last_confirmed = datetime.utcnow()
                if confidence > existing.confidence:
                    existing.confidence = confidence
                session.commit()
                return {"id": existing.id, "status": "updated"}
                
            fact = UserFact(
                user_id=user_id,
                fact_type=FactType(fact_type),
                fact_text=fact_text,
                confidence=confidence,
                source_turn_id=source_turn_id
            )
            session.add(fact)
            session.commit()
            return {"id": fact.id, "status": "created"}
            
    def get_user_facts(self, user_id: str) -> list[dict]:
        with self.get_session() as session:
            facts = session.query(UserFact).filter(UserFact.user_id == user_id).all()
            return [{"id": f.id, "type": f.fact_type.value, "text": f.fact_text, "confidence": f.confidence} for f in facts]
            
    def get_facts_by_type(self, user_id: str, fact_type: str) -> list[dict]:
        with self.get_session() as session:
            facts = session.query(UserFact).filter(
                UserFact.user_id == user_id,
                UserFact.fact_type == FactType(fact_type)
            ).all()
            return [{"id": f.id, "text": f.fact_text, "confidence": f.confidence} for f in facts]
            
    def update_conversation_summary(self, conversation_id: str, summary: str) -> None:
        with self.get_session() as session:
            conv = session.query(Conversation).filter(Conversation.id == conversation_id).first()
            if conv:
                conv.summary_text = summary
                
    def get_all_conversations(self, user_id: str) -> list[dict]:
        with self.get_session() as session:
            convs = session.query(Conversation).filter(
                Conversation.user_id == user_id
            ).order_by(Conversation.last_turn_at.desc()).all()
            
            return [{
                "id": c.id, 
                "session_id": c.session_id, 
                "started_at": c.started_at.isoformat(),
                "last_turn_at": c.last_turn_at.isoformat(),
                "summary": c.summary_text,
                "turn_count": c.turn_count
            } for c in convs]
