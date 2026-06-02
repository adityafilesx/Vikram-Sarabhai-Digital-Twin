from langchain_core.tools import tool
from rag.retriever import SarabhaiRetriever
from memory.memory_retriever import MemoryRetriever
from persona.timeline_handler import TimelineHandler

@tool
def search_sarabhai_knowledge(query: str, doc_type: str = None, timeline_year: int = None) -> str:
    """Search Vikram Sarabhai's authentic knowledge corpus for information relevant to a query.
    Use this for any factual question about space, science, India's development, or Sarabhai's views.
    
    Args:
        query: The search query derived from user's question
        doc_type: Optional filter - one of: speech, paper, interview, book, institutional
        timeline_year: Optional year to restrict search to documents from before that year
    """
    retriever = SarabhaiRetriever()
    result = retriever.retrieve(query, doc_type_filter=doc_type, timeline_year=timeline_year)
    
    if not result.chunks:
        return "No relevant historical documents found."
        
    formatted = result.combined_context + "\n\nSources: " + ", ".join(result.citations)
    return formatted

@tool  
def recall_user_memory(user_id: str, current_query: str, conversation_id: str) -> str:
    """Retrieve what is known about this user from past conversations.
    Use this always at the start of reasoning to personalize responses.
    
    Args:
        user_id: The current user's ID
        current_query: The current query to find relevant memories for
        conversation_id: Current conversation ID for recent context
    """
    retriever = MemoryRetriever()
    return retriever.build_memory_context(user_id, current_query, conversation_id)

@tool
def get_era_context(year: int) -> str:
    """Get historical context about India and Sarabhai's work in a specific year.
    Use this when user asks about a specific time period.
    
    Args:
        year: The year to get context for (e.g., 1962, 1968)
    """
    handler = TimelineHandler()
    ctx = handler.get_era_context(year)
    if not ctx:
        return f"No specific historical context available for {year}."
        
    return ctx.era_description + "\n" + handler.build_temporal_constraint(year)

@tool
def search_topic_broadly(topic: str) -> str:
    """Search the knowledge corpus broadly by topic rather than semantic similarity.
    Best for mission planning where you need comprehensive coverage of a theme.
    
    Args:
        topic: One of: space_programme, education, nuclear_energy, cosmic_rays, 
               institution_building, national_development, technology_policy
    """
    retriever = SarabhaiRetriever()
    result = retriever.retrieve_for_topic(topic)
    
    if not result.chunks:
        return f"No broad documents found for topic: {topic}."
        
    return result.combined_context

# List of all tools for the agent to bind
ALL_TOOLS = [search_sarabhai_knowledge, recall_user_memory, get_era_context, search_topic_broadly]
