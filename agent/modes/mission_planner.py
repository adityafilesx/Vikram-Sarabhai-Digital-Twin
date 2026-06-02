from pydantic import BaseModel, Field
from typing import List, Dict

class MissionPlan(BaseModel):
    mission_title: str = Field(description="Inspiring title for the mission")
    sarabhai_framing: str = Field(description="How Sarabhai frames why this matters conceptually")
    objectives: List[str] = Field(description="3-5 specific measurable objectives")
    human_capital: List[str] = Field(description="People and skills needed")
    technology_resources: List[str] = Field(description="Tech and infrastructure needed")
    key_challenges: List[str] = Field(description="Technical, political, social challenges")
    national_impact: Dict[str, str] = Field(description="Dict with short_term, medium_term, long_term keys")
    roadmap: Dict[str, str] = Field(description="Dict with phase_1_year_1, phase_2_years_1_5, phase_3_years_5_20 keys")
    historical_parallel: str = Field(description="Sarabhai's own similar historical challenge")
    first_action: str = Field(description="Single most important first step")

class MissionPlanner:
    MISSION_SYSTEM_PROMPT = """
You are acting as Dr. Vikram Sarabhai in Mission Director mode.
The user is not just asking a question; they want to design a mission or build a complex system.
You must output your response STRICTLY as a JSON object matching the requested schema.
Your plan must be highly structured, rigorous, and practical, while reflecting your visionary approach to project management (leapfrogging technology, self-reliance, societal impact).
"""

    def format_for_gradio(self, plan: MissionPlan) -> str:
        """Format the mission plan as clean Markdown for display in Gradio."""
        md = [
            f"# 🚀 Mission: {plan.mission_title}",
            "",
            f"*{plan.sarabhai_framing}*",
            "",
            "## 🎯 Objectives",
        ]
        for obj in plan.objectives:
            md.append(f"- {obj}")
            
        md.extend([
            "",
            "## 👥 Human Capital Required",
        ])
        for hc in plan.human_capital:
            md.append(f"- {hc}")
            
        md.extend([
            "",
            "## 🔧 Technology & Resources",
        ])
        for tr in plan.technology_resources:
            md.append(f"- {tr}")
            
        md.extend([
            "",
            "## ⚠️ Key Challenges",
        ])
        for kc in plan.key_challenges:
            md.append(f"- {kc}")
            
        md.extend([
            "",
            "## 🇮🇳 National Impact",
            f"- **Short Term:** {plan.national_impact.get('short_term', '')}",
            f"- **Medium Term:** {plan.national_impact.get('medium_term', '')}",
            f"- **Long Term:** {plan.national_impact.get('long_term', '')}",
            "",
            "## 🗺️ Execution Roadmap",
            f"- **Phase 1 (Year 1):** {plan.roadmap.get('phase_1_year_1', '')}",
            f"- **Phase 2 (Years 1-5):** {plan.roadmap.get('phase_2_years_1_5', '')}",
            f"- **Phase 3 (Years 5-20):** {plan.roadmap.get('phase_3_years_5_20', '')}",
            "",
            "## 📜 Historical Parallel",
            f"> {plan.historical_parallel}",
            "",
            "## ⚡ First Action",
            f"**{plan.first_action}**"
        ])
        
        return "\n".join(md)
