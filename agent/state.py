import operator
from typing import TypedDict, Optional, List, Annotated
from langgraph.graph.message import add_messages

class AgentState(TypedDict):
    # Input
    messages: Annotated[list, add_messages]   # Full conversation
    user_id: str
    session_id: str
    conversation_id: str
    
    # Classified
    intent: str          # factual/philosophical/mission/research/timeline/memory
    confidence: float
    timeline_year: Optional[int]
    mode: str            # conversational/mission_planning/research_mentor
    topics: List[str]
    
    # Retrieved context (reducers for parallel execution)
    retrieved_chunks: Annotated[List[str], operator.add]
    citations: Annotated[List[str], operator.add]
    retrieval_context: str
    
    # Memory context
    memory_context: str
    new_facts_extracted: List[dict]
    
    # Timeline
    era_context: str
    
    # Output
    final_response: str
    structured_output: Optional[dict]  # For mission/research modes
    
    # Internal
    error: Optional[str]
    node_trace: Annotated[List[str], operator.add]  # Which nodes ran, for debugging
