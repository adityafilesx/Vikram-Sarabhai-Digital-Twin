"""
Vikram Sarabhai Digital Twin — System Validation Script

Checks all components are properly configured and functional.
Run: python scripts/validate_system.py
"""
import os
import sys

# Ensure we run from project root
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(project_root)
sys.path.insert(0, project_root)

from dotenv import load_dotenv
load_dotenv()

def check(name, condition, detail=""):
    status = "✅" if condition else "❌"
    msg = f"  {status} {name}"
    if detail:
        msg += f" — {detail}"
    print(msg)
    return condition

def validate_environment():
    print("\n🔧 Environment Variables")
    ok = True
    ok &= check("GEMINI_API_KEYS", bool(os.getenv("GEMINI_API_KEYS")) or bool(os.getenv("GEMINI_API_KEY")))
    ok &= check("GOOGLE_API_KEY", bool(os.getenv("GOOGLE_API_KEY")))
    ok &= check("CHROMA_DB_PATH", bool(os.getenv("CHROMA_DB_PATH")), os.getenv("CHROMA_DB_PATH", "NOT SET"))
    ok &= check("SQLITE_DB_PATH", bool(os.getenv("SQLITE_DB_PATH")), os.getenv("SQLITE_DB_PATH", "NOT SET"))
    ok &= check("EMBEDDING_MODEL", bool(os.getenv("EMBEDDING_MODEL")), os.getenv("EMBEDDING_MODEL", "NOT SET"))
    ok &= check("GEMINI_MODEL", bool(os.getenv("GEMINI_MODEL")), os.getenv("GEMINI_MODEL", "NOT SET"))
    return ok

def validate_corpus():
    print("\n📚 Corpus")
    corpus_dir = os.getenv("CORPUS_DIR", "./data/corpus")
    ok = True
    total_docs = 0
    for doc_type in ["speeches", "papers", "interviews", "institutional"]:
        dir_path = os.path.join(corpus_dir, doc_type)
        if os.path.exists(dir_path):
            import json
            files = [f for f in os.listdir(dir_path) if f.endswith('.json') or f.endswith('.txt') or f.endswith('.pdf')]
            doc_count = 0
            for f in files:
                fpath = os.path.join(dir_path, f)
                if f.endswith('.json'):
                    try:
                        with open(fpath) as jf:
                            data = json.load(jf)
                            if isinstance(data, list):
                                doc_count += len(data)
                    except Exception:
                        pass
                else:
                    doc_count += 1
            total_docs += doc_count
            ok &= check(f"{doc_type}/", doc_count > 0, f"{doc_count} documents in {len(files)} files")
        else:
            ok &= check(f"{doc_type}/", False, "directory missing")
    
    check(f"Total corpus documents", total_docs >= 50, f"{total_docs} documents")
    return ok

def validate_imports():
    print("\n📦 Module Imports")
    ok = True
    
    modules = [
        ("rag.document_loader", "DocumentLoader"),
        ("rag.chunker", "Chunker"),
        ("rag.embedder", "Embedder"),
        ("rag.vector_store", "VectorStore"),
        ("rag.retriever", "SarabhaiRetriever"),
        ("rag.pipeline_runner", "run_pipeline"),
        ("persona.persona_engine", "PersonaEngine"),
        ("persona.timeline_handler", "TimelineHandler"),
        ("persona.reasoning_framework", "SARABHAI_REASONING_CHAIN"),
        ("memory.memory_db", "MemoryDatabase"),
        ("memory.memory_extractor", "MemoryExtractor"),
        ("memory.memory_retriever", "MemoryRetriever"),
        ("agent.state", "AgentState"),
        ("agent.intent_classifier", "IntentClassifier"),
        ("agent.tools", "ALL_TOOLS"),
        ("agent.agent_graph", "SarabhaiAgent"),
        ("agent.modes.mission_planner", "MissionPlanner"),
        ("agent.modes.research_mentor", "ResearchMentor"),
        ("backend.main", "app"),
    ]
    
    for mod_name, attr_name in modules:
        try:
            mod = __import__(mod_name, fromlist=[attr_name])
            getattr(mod, attr_name)
            ok &= check(f"{mod_name}.{attr_name}", True)
        except Exception as e:
            ok &= check(f"{mod_name}.{attr_name}", False, str(e)[:80])
    return ok

def validate_memory_db():
    print("\n🧠 Memory Database")
    ok = True
    try:
        from memory.memory_db import MemoryDatabase
        db = MemoryDatabase("sqlite:///:memory:")
        user = db.create_user("validate_user")
        ok &= check("Create user", "id" in user)
        conv = db.start_conversation(user["id"])
        ok &= check("Start conversation", "id" in conv)
        turn = db.add_turn(conv["id"], "user", "Hello")
        ok &= check("Add turn", "id" in turn)
        turns = db.get_recent_turns(conv["id"])
        ok &= check("Get recent turns", len(turns) == 1)
        db.save_fact(user["id"], "interest", "Space", 0.9)
        facts = db.get_user_facts(user["id"])
        ok &= check("Save and get facts", len(facts) == 1)
    except Exception as e:
        ok &= check("Memory DB", False, str(e)[:80])
    return ok

def validate_persona():
    print("\n🎭 Persona Engine")
    ok = True
    try:
        from persona.persona_engine import PersonaEngine
        engine = PersonaEngine()
        prompt = engine.build_prompt("Who are you?", "context", "memory", "early_career", "conversational")
        ok &= check("Build prompt", len(prompt) > 100)
        ok &= check("Era: early_career", engine.get_era_from_year(1947) == "early_career")
        ok &= check("Era: space_era", engine.get_era_from_year(1963) == "space_era")
        ok &= check("Era: institution_building", engine.get_era_from_year(1969) == "institution_building")
    except Exception as e:
        ok &= check("Persona Engine", False, str(e)[:80])
    return ok

def validate_chroma():
    print("\n🗄️ ChromaDB")
    ok = True
    try:
        from rag.vector_store import VectorStore
        vs = VectorStore()
        stats = vs.get_collection_stats()
        ok &= check("Collection accessible", "document_count" in stats, f"{stats.get('document_count', 0)} chunks stored")
    except Exception as e:
        ok &= check("ChromaDB", False, str(e)[:80])
    return ok

if __name__ == "__main__":
    print("=" * 60)
    print("  Vikram Sarabhai Digital Twin — System Validation")
    print("=" * 60)
    
    results = []
    results.append(("Environment", validate_environment()))
    results.append(("Corpus", validate_corpus()))
    results.append(("Imports", validate_imports()))
    results.append(("Memory DB", validate_memory_db()))
    results.append(("Persona", validate_persona()))
    results.append(("ChromaDB", validate_chroma()))
    
    print("\n" + "=" * 60)
    print("  Summary")
    print("=" * 60)
    all_ok = True
    for name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"  {status}: {name}")
        all_ok &= passed
    
    print()
    if all_ok:
        print("  🎉 All validations passed!")
    else:
        print("  ⚠️  Some validations failed. Review the output above.")
    
    sys.exit(0 if all_ok else 1)
