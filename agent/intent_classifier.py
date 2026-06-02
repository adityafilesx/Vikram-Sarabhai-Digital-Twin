import os
from pydantic import BaseModel, Field
from typing import Optional, List
from langchain_google_genai import ChatGoogleGenerativeAI
from dotenv import load_dotenv
from loguru import logger
from utils.api_rotator import rotator, with_retry

class IntentResult(BaseModel):
    intent: str = Field(description="One of: factual_question, philosophical_discussion, mission_planning, research_mentoring, timeline_query, memory_recall")
    confidence: float = Field(description="Confidence score between 0.0 and 1.0")
    timeline_hint: Optional[int] = Field(description="A specific year mentioned, if any", default=None)
    mode_hint: Optional[str] = Field(description="One of: mission_planning, research_mentor, or null", default=None)
    topics: List[str] = Field(description="List of detected themes", default_factory=list)
    reasoning: str = Field(description="Brief explanation for this classification")

class IntentClassifier:
    INTENT_SYSTEM_PROMPT = """
You are an intent classification engine for the Vikram Sarabhai Digital Twin.
Classify the user's latest message into one of these exact categories:

1. factual_question: User wants factual information about space, science, India, or Sarabhai's actual historical work.
2. philosophical_discussion: User wants to discuss ideas, values, vision, or have an open-ended intellectual conversation.
3. mission_planning: User wants to build, plan, or create something and wants strategic guidance. (Keywords: help me build, plan, design, create, start a)
4. research_mentoring: User wants feedback on a research idea, paper, or technical project. (Keywords: evaluate, review, critique, what do you think of my)
5. timeline_query: User explicitly mentions a year, era, or asks what Sarabhai thought at a specific time period.
6. memory_recall: User refers to a previous conversation or asks if the twin remembers something.

Output strictly according to the required schema.
"""

    def __init__(self):
        load_dotenv()
        self.model_name = os.getenv('GEMINI_MODEL', 'gemini-2.5-flash')
        
    def _get_structured_llm(self):
        llm = ChatGoogleGenerativeAI(
            model=self.model_name,
            api_key=rotator.get_current_key() or "",
            temperature=0.1
        )
        return llm.with_structured_output(IntentResult)
        
    def classify(self, message: str, conversation_history: list = None) -> IntentResult:
        logger.info(f"Classifying intent for message: '{message[:50]}...'")
        
        history_text = ""
        if conversation_history:
            # Take last 3 messages for context
            recent = conversation_history[-3:]
            formatted = []
            for msg in recent:
                role = msg.type if hasattr(msg, 'type') else msg.get('role', 'user') if isinstance(msg, dict) else 'user'
                content = getattr(msg, 'content', msg.get('content', '')) if isinstance(msg, dict) else getattr(msg, 'content', '')
                formatted.append(f"{role}: {content}")
            history_text = "\nContext:\n" + "\n".join(formatted)
            
        prompt = f"{self.INTENT_SYSTEM_PROMPT}{history_text}\n\nLatest Message: {message}"
        
        try:
            result = with_retry(
                self._get_structured_llm,
                lambda llm: llm.invoke(prompt)
            )
            logger.info(f"Classified as: {result.intent} (conf: {result.confidence})")
            return result
        except Exception as e:
            logger.error(f"Intent classification failed: {e}")
            # Fallback
            return IntentResult(
                intent="philosophical_discussion", 
                confidence=0.0,
                reasoning="Fallback due to error"
            )
