import os
import json
from loguru import logger
from langgraph.graph import StateGraph, START, END
from langchain_google_genai import ChatGoogleGenerativeAI
from dotenv import load_dotenv
from utils.api_rotator import rotator, with_retry

from agent.state import AgentState
from agent.intent_classifier import IntentClassifier
from agent.tools import search_sarabhai_knowledge, recall_user_memory, get_era_context, search_topic_broadly
from persona.persona_engine import PersonaEngine
from memory.memory_extractor import MemoryExtractor
from memory.memory_db import MemoryDatabase
from agent.modes.mission_planner import MissionPlanner, MissionPlan
from agent.modes.research_mentor import ResearchMentor, ResearchFeedback

def _get_msg_content(msg):
    return getattr(msg, 'content', msg.get('content', '')) if isinstance(msg, dict) else getattr(msg, 'content', '')

def _get_msg_role(msg):
    return msg.type if hasattr(msg, 'type') else msg.get('role', 'user') if isinstance(msg, dict) else 'user'

class SarabhaiAgent:
    def __init__(self):
        load_dotenv()
        self.model_name = os.getenv('GEMINI_MODEL', 'gemini-2.5-flash')
        
        self.intent_classifier = IntentClassifier()
        self.persona_engine = PersonaEngine()
        self.memory_extractor = MemoryExtractor()
        self.memory_db = MemoryDatabase()
        
        self.graph = self._build_graph()
        
    def _get_llm(self):
        return ChatGoogleGenerativeAI(
            model=self.model_name,
            api_key=rotator.get_current_key() or "",
            temperature=0.3
        )
        
    def _build_graph(self):
        workflow = StateGraph(AgentState)
        workflow.add_node("intent_node", self.intent_node)
        workflow.add_node("rag_node", self.rag_node)
        workflow.add_node("memory_node", self.memory_node)
        workflow.add_node("timeline_node", self.timeline_node)
        workflow.add_node("reasoning_node", self.reasoning_node)
        workflow.add_node("memory_update_node", self.memory_update_node)
        workflow.add_node("response_node", self.response_node)
        
        # Sequential routing: intent → rag → memory → timeline → reasoning → memory_update → response
        workflow.add_edge(START, "intent_node")
        workflow.add_edge("intent_node", "rag_node")
        workflow.add_edge("rag_node", "memory_node")
        workflow.add_edge("memory_node", "timeline_node")
        workflow.add_edge("timeline_node", "reasoning_node")
        workflow.add_edge("reasoning_node", "memory_update_node")
        workflow.add_edge("memory_update_node", "response_node")
        workflow.add_edge("response_node", END)
        
        return workflow.compile()

    def intent_node(self, state: AgentState):
        logger.info("Executing intent_node")
        last_msg = _get_msg_content(state['messages'][-1]) if state['messages'] else ""
        
        result = self.intent_classifier.classify(last_msg, state['messages'])
        
        # Override mode if provided by UI
        mode = state.get('mode', 'conversational')
        if result.mode_hint and mode == 'conversational':
            mode = result.mode_hint
            
        return {
            "intent": result.intent,
            "confidence": result.confidence,
            "timeline_year": result.timeline_hint or state.get('timeline_year'),
            "mode": mode,
            "topics": result.topics,
            "node_trace": ["intent_node"]
        }

    def rag_node(self, state: AgentState):
        logger.info("Executing rag_node")
        try:
            last_msg = _get_msg_content(state['messages'][-1]) if state['messages'] else ""
            
            if state.get('mode') == 'mission_planning' and state.get('topics'):
                res = search_topic_broadly.invoke({"topic": state['topics'][0]})
            else:
                res = search_sarabhai_knowledge.invoke({"query": last_msg})
                
            return {
                "retrieval_context": res,
                "node_trace": ["rag_node"]
            }
        except Exception as e:
            logger.error(f"RAG node failed: {e}")
            return {
                "retrieval_context": "",
                "node_trace": ["rag_node"]
            }

    def memory_node(self, state: AgentState):
        logger.info("Executing memory_node")
        try:
            last_msg = _get_msg_content(state['messages'][-1]) if state['messages'] else ""
            res = recall_user_memory.invoke({
                "user_id": state['user_id'], 
                "current_query": last_msg, 
                "conversation_id": state['conversation_id']
            })
            return {
                "memory_context": res,
                "node_trace": ["memory_node"]
            }
        except Exception as e:
            logger.error(f"Memory node failed: {e}")
            return {
                "memory_context": "",
                "node_trace": ["memory_node"]
            }
        
    def timeline_node(self, state: AgentState):
        logger.info("Executing timeline_node")
        year = state.get('timeline_year')
        if year and year < 1971:
            try:
                res = get_era_context.invoke({"year": year})
                return {
                    "era_context": res,
                    "node_trace": ["timeline_node"]
                }
            except Exception as e:
                logger.error(f"Timeline node failed: {e}")
        return {"node_trace": ["timeline_node"]}

    def reasoning_node(self, state: AgentState):
        logger.info("Executing reasoning_node")
        last_msg = _get_msg_content(state['messages'][-1])
        
        # Build prompt
        timeline_year = state.get('timeline_year')
        era_key = None
        if timeline_year and timeline_year < 1971:
            era_key = self.persona_engine.get_era_from_year(timeline_year)
        
        system_prompt = self.persona_engine.build_prompt(
            user_query=last_msg,
            retrieved_context=state.get('retrieval_context', ''),
            memory_context=state.get('memory_context', ''),
            timeline_period=era_key,
            mode=state.get('mode', 'conversational')
        )
        
        # Execute based on mode
        mode = state.get('mode', 'conversational')
        
        try:
            if mode == 'mission_planning':
                result = with_retry(
                    self._get_llm,
                    lambda llm: llm.with_structured_output(MissionPlan).invoke(f"{system_prompt}\n\nUser Objective: {last_msg}")
                )
                planner = MissionPlanner()
                response = planner.format_for_gradio(result)
                return {"final_response": response, "structured_output": result.model_dump(), "node_trace": ["reasoning_node"]}
                
            elif mode == 'research_mentor':
                result = with_retry(
                    self._get_llm,
                    lambda llm: llm.with_structured_output(ResearchFeedback).invoke(f"{system_prompt}\n\nResearch Idea: {last_msg}")
                )
                mentor = ResearchMentor()
                response = mentor.format_for_gradio(result)
                return {"final_response": response, "structured_output": result.model_dump(), "node_trace": ["reasoning_node"]}
                
            else: # conversational
                messages = [{"role": "system", "content": system_prompt}] + state['messages']
                result = with_retry(
                    self._get_llm,
                    lambda llm: llm.invoke(messages)
                )
                return {"final_response": result.content, "structured_output": None, "node_trace": ["reasoning_node"]}
                
        except Exception as e:
            logger.error(f"Reasoning node failed: {e}")
            return {"final_response": "I apologize, but I encountered an error while formulating my thoughts. Please try your question again.", "error": str(e), "node_trace": ["reasoning_node"]}

    def memory_update_node(self, state: AgentState):
        logger.info("Executing memory_update_node")
        try:
            last_msg = _get_msg_content(state['messages'][-1])
            history = "\n".join([f"{_get_msg_role(m)}: {_get_msg_content(m)}" for m in state['messages'][-5:]])
            
            ext_result = self.memory_extractor.extract_facts(last_msg, history)
            
            new_facts = []
            for fact in ext_result.facts:
                if self.memory_extractor.should_store_fact(fact):
                    saved = self.memory_db.save_fact(
                        user_id=state['user_id'],
                        fact_type=fact.fact_type,
                        fact_text=fact.fact_text,
                        confidence=fact.confidence
                    )
                    new_facts.append(saved)
                    
            # Optional: check if we need to summarize
            turns = self.memory_db.get_recent_turns(state['conversation_id'], 10)
            if len(turns) >= 10: # Simple trigger
                summary = self.memory_extractor.summarize_conversation([f"{t['role']}: {t['content']}" for t in turns])
                self.memory_db.update_conversation_summary(state['conversation_id'], summary)
                
            return {"new_facts_extracted": new_facts, "node_trace": ["memory_update_node"]}
        except Exception as e:
            logger.error(f"Memory update failed: {e}")
            return {"new_facts_extracted": [], "node_trace": ["memory_update_node"]}

    def response_node(self, state: AgentState):
        logger.info("Executing response_node")
        return {"node_trace": ["response_node"]} # final_response is already set
        
    async def run_agent(self, state: dict) -> dict:
        """Entry point for the backend"""
        return await self.graph.ainvoke(state)
