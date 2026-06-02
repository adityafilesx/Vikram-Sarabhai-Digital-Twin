import pytest
from memory.memory_db import MemoryDatabase

@pytest.fixture
def test_db():
    """Use in-memory sqlite for testing."""
    db = MemoryDatabase("sqlite:///:memory:")
    return db

def test_create_user_and_conversation(test_db):
    user = test_db.create_user(username="test_user", display_name="Test User")
    assert user["username"] == "test_user"
    assert "id" in user
    
    conv = test_db.start_conversation(user_id=user["id"])
    assert conv["user_id"] == user["id"]
    assert "id" in conv

def test_add_turn_and_get_history(test_db):
    user = test_db.create_user("test_user_2")
    conv = test_db.start_conversation(user["id"])
    
    test_db.add_turn(conv["id"], "user", "Hello")
    test_db.add_turn(conv["id"], "assistant", "Greetings")
    
    turns = test_db.get_recent_turns(conv["id"])
    assert len(turns) == 2
    assert turns[0]["role"] == "user"
    assert turns[1]["role"] == "assistant"

def test_save_and_get_facts(test_db):
    user = test_db.create_user("test_user_3")
    test_db.save_fact(user["id"], "interest", "Cosmic Rays", 0.9)
    test_db.save_fact(user["id"], "project", "Building a sounding rocket", 0.95)
    
    facts = test_db.get_user_facts(user["id"])
    assert len(facts) == 2
    types = [f["type"] for f in facts]
    assert "interest" in types
    assert "project" in types

def test_fact_deduplication(test_db):
    user = test_db.create_user("test_user_4")
    test_db.save_fact(user["id"], "interest", "Space Science", 0.8)
    test_db.save_fact(user["id"], "interest", "Space Science", 0.95)
    
    facts = test_db.get_user_facts(user["id"])
    assert len(facts) == 1
    assert facts[0]["confidence"] == 0.95  # Should have updated to higher confidence

def test_get_user(test_db):
    test_db.create_user("lookup_user", "Lookup User")
    user = test_db.get_user("lookup_user")
    assert user is not None
    assert user["username"] == "lookup_user"
    assert user["display_name"] == "Lookup User"
    
    missing = test_db.get_user("nonexistent_user")
    assert missing is None

def test_conversation_summary(test_db):
    user = test_db.create_user("summary_user")
    conv = test_db.start_conversation(user["id"])
    test_db.update_conversation_summary(conv["id"], "Test conversation about cosmic rays")
    
    convs = test_db.get_all_conversations(user["id"])
    assert len(convs) == 1
    assert convs[0]["summary"] == "Test conversation about cosmic rays"
