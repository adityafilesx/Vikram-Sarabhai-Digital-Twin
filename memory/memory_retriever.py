import numpy as np
from loguru import logger
from memory.memory_db import MemoryDatabase
from rag.embedder import Embedder

class MemoryRetriever:
    def __init__(self):
        self.db = MemoryDatabase()
        self.embedder = Embedder()
        self.fact_embeddings_cache = {} # {user_id: {fact_id: embedding}}
        
    def build_memory_context(self, user_id: str, current_query: str, conversation_id: str) -> str:
        """Get facts, embed query, cosine similarity, top 5 relevant facts, format as context string"""
        facts = self.db.get_user_facts(user_id)
        if not facts:
            return ""
            
        # Get query embedding
        try:
            query_emb = self.embedder.embed_query(current_query)
        except Exception as e:
            logger.error(f"Failed to embed query for memory retrieval: {e}")
            return ""
            
        # Ensure we have embeddings for all facts (cache them)
        if user_id not in self.fact_embeddings_cache:
            self.fact_embeddings_cache[user_id] = {}
            
        user_cache = self.fact_embeddings_cache[user_id]
        
        scored_facts = []
        for fact in facts:
            fact_id = fact["id"]
            if fact_id not in user_cache:
                try:
                    user_cache[fact_id] = self.embedder.embed_text(fact["text"])
                except Exception as e:
                    logger.error(f"Failed to embed fact {fact_id}: {e}")
                    continue
                    
            fact_emb = user_cache[fact_id]
            sim = self._cosine_similarity(query_emb, fact_emb)
            scored_facts.append((sim, fact))
            
        # Sort and get top 5
        scored_facts.sort(key=lambda x: x[0], reverse=True)
        top_facts = [f for score, f in scored_facts[:5] if score > 0.4] # Apply minimum similarity threshold
        
        if not top_facts:
            return ""
            
        # Format context
        context_parts = ["What I know about you from our previous conversations:"]
        for f in top_facts:
            context_parts.append(f"- [{f['type'].upper()}] {f['text']}")
            
        # Add recent conversation context
        recent_turns = self.db.get_recent_turns(conversation_id, n=3)
        if recent_turns:
            context_parts.append("\nRecent conversation context:")
            for turn in recent_turns:
                context_parts.append(f"{turn['role'].capitalize()}: {turn['content']}")
                
        return "\n".join(context_parts)
    
    def format_memory_for_display(self, user_id: str) -> dict:
        """Return dict for Gradio memory dashboard."""
        facts = self.db.get_user_facts(user_id)
        
        display_data = {
            "interests": [],
            "projects": [],
            "goals": [],
            "background": [],
            "conversation_count": 0,
            "last_active": "Never"
        }
        
        for f in facts:
            ftype = f["type"]
            if ftype in display_data:
                display_data[ftype].append(f["text"])
            elif ftype in ("question", "belief"):
                display_data["background"].append(f["text"]) # Roll these into background for display
                
        user = self.db.get_user(user_id)
        if user:
            # We'd ideally fetch from DB, but for simplicity we just return placeholder counts
            # The full implementation would query the user's conversation count and last_active.
            pass
            
        return display_data
    
    def build_memory_graph_data(self, user_id: str) -> dict:
        """Build NetworkX-compatible {nodes, edges} for Plotly visualization"""
        # A simple graph: User -> Topics -> Facts
        nodes = [{"id": user_id, "label": "You", "type": "user", "weight": 20}]
        edges = []
        
        facts = self.db.get_user_facts(user_id)
        for i, f in enumerate(facts):
            node_id = f"fact_{i}"
            nodes.append({
                "id": node_id,
                "label": f["text"][:30] + "..." if len(f["text"]) > 30 else f["text"],
                "type": f["type"],
                "weight": f["confidence"] * 10
            })
            edges.append({"source": user_id, "target": node_id, "weight": f["confidence"]})
            
        return {"nodes": nodes, "edges": edges}
    
    @staticmethod
    def _cosine_similarity(a: list[float], b: list[float]) -> float:
        """Compute cosine similarity between two vectors"""
        a = np.array(a)
        b = np.array(b)
        norm_a = np.linalg.norm(a)
        norm_b = np.linalg.norm(b)
        if norm_a == 0 or norm_b == 0:
            return 0.0
        return float(np.dot(a, b) / (norm_a * norm_b))
