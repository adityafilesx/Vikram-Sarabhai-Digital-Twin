import re
from pydantic import BaseModel, Field
from typing import Optional, List
from loguru import logger

class IntentResult(BaseModel):
    intent: str = Field(description="One of: factual_question, philosophical_discussion, mission_planning, research_mentoring, timeline_query, memory_recall")
    confidence: float = Field(description="Confidence score between 0.0 and 1.0")
    timeline_hint: Optional[int] = Field(description="A specific year mentioned, if any", default=None)
    mode_hint: Optional[str] = Field(description="One of: mission_planning, research_mentor, or null", default=None)
    topics: List[str] = Field(description="List of detected themes", default_factory=list)
    reasoning: str = Field(description="Brief explanation for this classification")

class IntentClassifier:
    """Fast keyword-based intent classifier — no LLM call needed."""

    # Patterns ordered from most specific to least specific
    PATTERNS = [
        {
            "intent": "memory_recall",
            "keywords": [r"\bremember\b", r"\blast time\b", r"\bprevious\b", r"\bbefore\b", r"\byou said\b", r"\bwe discussed\b", r"\bwe talked\b"],
            "mode_hint": None,
        },
        {
            "intent": "timeline_query",
            "keywords": [r"\b(19\d{2}|20[012]\d)\b", r"\bin the \d{4}s?\b", r"\bera\b", r"\bdecade\b", r"\bback then\b", r"\bat that time\b"],
            "mode_hint": None,
        },
        {
            "intent": "mission_planning",
            "keywords": [r"\bhelp me (build|plan|design|create|start|launch)\b", r"\bhow (do|can|should) (i|we) (build|plan|design|create|start)\b", r"\bstrateg(y|ic)\b", r"\broadmap\b", r"\bblueprint\b", r"\bmission plan\b"],
            "mode_hint": "mission_planning",
        },
        {
            "intent": "research_mentoring",
            "keywords": [r"\b(evaluate|review|critique|assess|feedback)\b", r"\bwhat do you think of\b", r"\bmy (research|paper|project|thesis|idea)\b", r"\bmentor\b"],
            "mode_hint": "research_mentor",
        },
        {
            "intent": "factual_question",
            "keywords": [r"\b(what|when|where|who|how many|which)\b.*\?", r"\btell me about\b", r"\bexplain\b", r"\bwhat (is|was|are|were)\b", r"\bfact\b", r"\bhistory\b", r"\bbiograph\b", r"\beducat\b", r"\bfound(ed|ing)\b", r"\bISRO\b", r"\bPRL\b", r"\bIIM\b"],
            "mode_hint": None,
        },
    ]

    def __init__(self):
        pass  # No LLM needed

    def classify(self, message: str, conversation_history: list = None) -> IntentResult:
        logger.info(f"Classifying intent for message: '{message[:50]}...'")
        msg_lower = message.lower()

        # Extract year hints
        year_match = re.search(r"\b(19[2-9]\d|20[0-2]\d)\b", message)
        timeline_hint = int(year_match.group(1)) if year_match else None

        # Match patterns
        for pattern in self.PATTERNS:
            for kw in pattern["keywords"]:
                if re.search(kw, msg_lower):
                    result = IntentResult(
                        intent=pattern["intent"],
                        confidence=0.85,
                        timeline_hint=timeline_hint,
                        mode_hint=pattern["mode_hint"],
                        topics=self._extract_topics(msg_lower),
                        reasoning=f"Matched keyword pattern for {pattern['intent']}"
                    )
                    logger.info(f"Classified as: {result.intent} (conf: {result.confidence})")
                    return result

        # Default: philosophical discussion (Sarabhai's strength)
        result = IntentResult(
            intent="philosophical_discussion",
            confidence=0.7,
            timeline_hint=timeline_hint,
            mode_hint=None,
            topics=self._extract_topics(msg_lower),
            reasoning="No specific pattern matched, defaulting to philosophical discussion"
        )
        logger.info(f"Classified as: {result.intent} (conf: {result.confidence})")
        return result

    def _extract_topics(self, msg: str) -> list[str]:
        """Extract topic keywords from the message."""
        topic_map = {
            "space": ["space", "rocket", "satellite", "orbit", "launch", "isro", "nasa"],
            "education": ["education", "university", "student", "learning", "iim", "school", "teach"],
            "science": ["science", "research", "physics", "cosmic", "ray", "experiment"],
            "technology": ["technology", "tech", "computer", "ai", "nuclear", "atomic"],
            "leadership": ["leadership", "leader", "manage", "vision", "inspire"],
            "india": ["india", "indian", "nation", "country", "development"],
            "philosophy": ["philosophy", "think", "believe", "value", "meaning", "purpose"],
            "institution": ["institution", "prl", "isro", "iim", "organization", "found"],
        }
        found = []
        for topic, keywords in topic_map.items():
            if any(kw in msg for kw in keywords):
                found.append(topic)
        return found or ["general"]
