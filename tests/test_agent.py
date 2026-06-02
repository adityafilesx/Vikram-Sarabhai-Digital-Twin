import pytest
from agent.state import AgentState

def test_agent_state_dict():
    # Just verifying the TypedDict can be instantiated with default fields
    state = AgentState(
        messages=[{"role": "user", "content": "Hello"}],
        user_id="user_1",
        session_id="session_1",
        conversation_id="conv_1",
        intent="factual_question",
        confidence=0.9,
        timeline_year=None,
        mode="conversational",
        topics=["space"],
        retrieved_chunks=[],
        citations=[],
        retrieval_context="",
        memory_context="",
        new_facts_extracted=[],
        era_context="",
        final_response="",
        structured_output=None,
        error=None,
        node_trace=[]
    )
    
    assert state["intent"] == "factual_question"
    assert len(state["messages"]) == 1
