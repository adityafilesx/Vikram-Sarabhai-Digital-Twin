import os
import json
from dataclasses import dataclass, field
from google import genai
from google.genai import types
from dotenv import load_dotenv
from loguru import logger
from utils.api_rotator import rotator, with_retry, with_model_fallback

@dataclass
class ExtractedFact:
    fact_type: str  # interest/project/goal/question/belief/background
    fact_text: str
    confidence: float
    reasoning: str

@dataclass
class ExtractionResult:
    facts: list[ExtractedFact]
    topics_discussed: list[str]
    conversation_mood: str

class MemoryExtractor:
    EXTRACTION_PROMPT = """Analyze the latest user message in the context of the conversation history.
Extract concrete facts about the user. 
Respond ONLY in valid JSON matching the following schema precisely:

{
  "facts": [
    {
      "fact_type": "interest|project|goal|question|belief|background",
      "fact_text": "A clear, concise, factual statement about the user. E.g., 'User is building a weather satellite.'",
      "confidence": 0.9,
      "reasoning": "Why you extracted this fact from the text."
    }
  ],
  "topics_discussed": ["list", "of", "topic", "strings"],
  "conversation_mood": "curious|collaborative|seeking_advice|philosophical"
}

If no new facts are found, return an empty list for "facts".
"""

    SUMMARY_PROMPT = """Summarize the key facts, topics discussed, and what this person is working on, based on the following conversation history. Keep it to 3 sentences maximum."""

    def __init__(self):
        load_dotenv()
        self.model = os.getenv('GEMINI_MODEL', 'gemini-2.5-flash')
        self.confidence_threshold = float(os.getenv('MEMORY_CONFIDENCE_THRESHOLD', '0.75'))

    def _get_client(self):
        return genai.Client(api_key=rotator.get_current_key() or "")
    
    def extract_facts(self, user_message: str, conversation_history: str) -> ExtractionResult:
        """Call Gemini, parse JSON response, return facts with confidence >= 0.5"""
        prompt = f"{self.EXTRACTION_PROMPT}\n\nRecent History:\n{conversation_history}\n\nLatest User Message:\n{user_message}"
        
        def _build_and_call(model_name: str):
            client = genai.Client(api_key=rotator.get_current_key() or "")
            return client.models.generate_content(
                model=model_name,
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    temperature=0.1
                )
            )
            
        try:
            # We enforce JSON output using response_mime_type
            response = with_model_fallback(self.model, _build_and_call)
            
            data = json.loads(response.text)
            
            facts = []
            for f in data.get("facts", []):
                conf = float(f.get("confidence", 0.0))
                if conf >= 0.5:
                    facts.append(ExtractedFact(
                        fact_type=f.get("fact_type", "background"),
                        fact_text=f.get("fact_text", ""),
                        confidence=conf,
                        reasoning=f.get("reasoning", "")
                    ))
                    
            return ExtractionResult(
                facts=facts,
                topics_discussed=data.get("topics_discussed", []),
                conversation_mood=data.get("conversation_mood", "neutral")
            )
            
        except Exception as e:
            logger.error(f"Failed to extract facts: {e}")
            return ExtractionResult(facts=[], topics_discussed=[], conversation_mood="neutral")
            
    def should_store_fact(self, fact: ExtractedFact) -> bool:
        """Return True if confidence >= threshold OR fact_type in (project, goal)"""
        if fact.fact_type in ("project", "goal"):
            return True
        return fact.confidence >= self.confidence_threshold
    
    def summarize_conversation(self, turns: list[str]) -> str:
        """Generate 3-sentence summary using Gemini"""
        history_text = "\n".join(turns)
        prompt = f"{self.SUMMARY_PROMPT}\n\nConversation:\n{history_text}"
        
        def _build_and_call(model_name: str):
            client = genai.Client(api_key=rotator.get_current_key() or "")
            return client.models.generate_content(
                model=model_name,
                contents=prompt,
                config=types.GenerateContentConfig(temperature=0.3)
            )
            
        try:
            response = with_model_fallback(self.model, _build_and_call)
            return response.text.strip()
        except Exception as e:
            logger.error(f"Failed to summarize conversation: {e}")
            return ""
