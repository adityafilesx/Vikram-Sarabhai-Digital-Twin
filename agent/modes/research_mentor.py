from pydantic import BaseModel, Field
from typing import List, Dict

class ResearchFeedback(BaseModel):
    verdict_headline: str = Field(description="One sentence honest assessment")
    strengths: List[str] = Field(description="What is scientifically sound")
    critical_gaps: List[str] = Field(description="What is missing or unvalidated")
    methodology_suggestions: List[str] = Field(description="Specific approaches or techniques")
    literature_connections: List[str] = Field(description="Related historical work or physics principles")
    institutional_considerations: List[str] = Field(description="What organizational structures need building")
    next_steps: List[Dict[str, str]] = Field(description="List of dicts with 'action', 'priority', 'timeframe'")
    sarabhai_verdict: str = Field(description="Full paragraph verdict in Sarabhai's voice")
    encouragement: str = Field(description="What genuinely excites Sarabhai about this")

class ResearchMentor:
    MENTOR_SYSTEM_PROMPT = """
You are acting as Dr. Vikram Sarabhai evaluating a research idea with the rigor of a PhD supervisor who has run one of India's greatest research institutions.
You must output your response STRICTLY as a JSON object matching the requested schema.
Evaluate the idea with extreme rigor but unyielding encouragement. Point out critical flaws scientifically, but immediately suggest how they might overcome them. Ground suggestions in historical precedent.
"""

    def format_for_gradio(self, feedback: ResearchFeedback) -> str:
        """Format the research feedback as clean Markdown for display in Gradio."""
        md = [
            f"# 🔬 Research Review: **{feedback.verdict_headline}**",
            "",
            "## ✅ Scientific Strengths",
        ]
        for s in feedback.strengths:
            md.append(f"- {s}")
            
        md.extend([
            "",
            "## ⚠️ Critical Gaps to Address",
        ])
        for g in feedback.critical_gaps:
            md.append(f"- {g}")
            
        md.extend([
            "",
            "## 🛠️ Methodological Suggestions",
        ])
        for m in feedback.methodology_suggestions:
            md.append(f"- {m}")
            
        md.extend([
            "",
            "## 📚 Historical/Literature Connections",
        ])
        for l in feedback.literature_connections:
            md.append(f"- {l}")
            
        md.extend([
            "",
            "## 🏛️ Institutional & Resource Considerations",
        ])
        for i in feedback.institutional_considerations:
            md.append(f"- {i}")
            
        md.extend([
            "",
            "## 🛤️ Recommended Next Steps",
        ])
        for step in feedback.next_steps:
            action = step.get('action', '')
            priority = step.get('priority', '')
            timeframe = step.get('timeframe', '')
            md.append(f"- **[{priority.upper()}]** {action} *(Timeline: {timeframe})*")
            
        md.extend([
            "",
            "---",
            "## 🗣️ Dr. Sarabhai's Verdict",
            f"*{feedback.sarabhai_verdict}*",
            "",
            "## 💡 Final Encouragement",
            f"> {feedback.encouragement}"
        ])
        
        return "\n".join(md)
