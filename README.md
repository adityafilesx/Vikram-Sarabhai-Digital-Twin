# 🚀 Vikram Sarabhai Digital Twin

An agentic AI simulation of **Dr. Vikram Sarabhai** — the father of the Indian space programme — built with modern AI infrastructure.

This Digital Twin doesn't just answer questions about Sarabhai. It *reasons* like him, using a five-step framework grounded in his documented thought process: scientific understanding, feasibility assessment, human-societal dimension, national strategic implications, and long-horizon recommendations.

## Architecture

```
User → Gradio UI → FastAPI Backend → LangGraph Agent → Gemini 2.5 Flash
                                          ↓
                              ┌───────────┼───────────┐
                              ▼           ▼           ▼
                          RAG Engine   Memory     Persona
                         (ChromaDB)   (SQLite)    Engine
```

**Stack:**
- **LLM:** Google Gemini 2.5 Flash (via `google-genai` SDK)
- **Agent Framework:** LangGraph (StateGraph with 7 nodes)
- **RAG:** ChromaDB + Gemini text-embedding-004
- **Memory:** SQLite via SQLAlchemy (persistent user facts, conversation history)
- **Backend:** FastAPI with SSE streaming
- **Frontend:** Gradio 5 with custom deep-space theme
- **Persona:** 5-step chain-of-thought reasoning + timeline-aware constraints

## Features

### 🗣️ Conversational Mode
Ask Dr. Sarabhai anything about space science, India's development, institution building, or technology policy. Responses are grounded in his authentic corpus (speeches, papers, interviews).

### 📋 Mission Planning Mode
Present an objective ("I want to build a satellite for rural education") and receive a structured mission plan with objectives, resources, roadmap, and historical parallels from Sarabhai's own work.

### 🔬 Research Mentor Mode
Share a research idea and receive rigorous-yet-encouraging feedback: strengths, critical gaps, methodology suggestions, and a full verdict in Sarabhai's voice.

### 🕰️ Timeline Mode
Speak with Sarabhai from specific eras:
- **1947–1955:** Young physicist at Cambridge and PRL
- **1956–1965:** INCOSPAR founder, first sounding rockets
- **1966–1971:** ISRO chairman, institution builder at peak influence

### 🧠 Persistent Memory
The Twin remembers you across sessions — your interests, projects, goals, and discussion history — personalizing every interaction.

## Quick Start

```bash
# 1. Clone and install
cd sarabhai-digital-twin
pip install -r requirements.txt

# 2. Configure
cp .env.example .env
# Edit .env with your GEMINI_API_KEY

# 3. Add corpus data
# Place PDFs/TXTs in data/corpus/{speeches,papers,interviews,institutional}/

# 4. Ingest corpus into ChromaDB
python -m rag.pipeline_runner

# 5. Launch backend
uvicorn backend.main:app --host 0.0.0.0 --port 8000

# 6. Launch frontend (separate terminal)
python frontend/app.py
```

Open `http://localhost:7860` in your browser.

## Project Structure

```
sarabhai-digital-twin/
├── rag/                    # RAG pipeline (load → chunk → embed → store → retrieve)
├── persona/                # Persona engine, reasoning framework, timeline handler
├── memory/                 # SQLite memory DB, fact extractor, memory retriever
├── agent/                  # LangGraph agent graph, intent classifier, tools
│   └── modes/              # Mission Planner, Research Mentor
├── backend/                # FastAPI server
├── frontend/               # Gradio UI (chat, memory dashboard)
├── data/corpus/            # Source documents (not included — add your own)
├── tests/                  # Unit and integration tests
└── scripts/                # Utility scripts
```

### Module Breakdown

#### 🖥️ [backend/](file:///Users/aditya1981/Documents/Vikram%20Sarabhai%20Digital%20Twin/backend)
Handles HTTP communication and API routing.
- **[main.py](file:///Users/aditya1981/Documents/Vikram%20Sarabhai%20Digital%20Twin/backend/main.py)**: The FastAPI server that orchestrates request handling, serves the Static UI files, exposes memory dashboard endpoints, and invokes the LangGraph agent for generating streaming text responses.

#### 🧠 [memory/](file:///Users/aditya1981/Documents/Vikram%20Sarabhai%20Digital%20Twin/memory)
Manages persistent state and personalization profiles across sessions.
- **[memory_db.py](file:///Users/aditya1981/Documents/Vikram%20Sarabhai%20Digital%20Twin/memory/memory_db.py)**: SQLite database schema and interactions for user profiles, session tracking, and chat histories.
- **[memory_extractor.py](file:///Users/aditya1981/Documents/Vikram%20Sarabhai%20Digital%20Twin/memory/memory_extractor.py)**: Leverages Gemini to dynamically distill user interests, projects, and goals from conversation transcripts in the background.
- **[memory_retriever.py](file:///Users/aditya1981/Documents/Vikram%20Sarabhai%20Digital%20Twin/memory/memory_retriever.py)**: Prepares profile structures and formatting logic for memory visualization nodes in the frontend graphs.

#### 🔍 [rag/](file:///Users/aditya1981/Documents/Vikram%20Sarabhai%20Digital%20Twin/rag)
Powering semantic grounding via Retrieval-Augmented Generation.
- **[document_loader.py](file:///Users/aditya1981/Documents/Vikram%20Sarabhai%20Digital%20Twin/rag/document_loader.py)** & **[chunker.py](file:///Users/aditya1981/Documents/Vikram%20Sarabhai%20Digital%20Twin/rag/chunker.py)**: Read, clean, and chunk multi-format historical texts.
- **[embedder.py](file:///Users/aditya1981/Documents/Vikram%20Sarabhai%20Digital%20Twin/rag/embedder.py)**: Interfaces with Gemini's text-embeddings models.
- **[vector_store.py](file:///Users/aditya1981/Documents/Vikram%20Sarabhai%20Digital%20Twin/rag/vector_store.py)**: Manages vector indexing and similarity searches using local ChromaDB storage.
- **[pipeline_runner.py](file:///Users/aditya1981/Documents/Vikram%20Sarabhai%20Digital%20Twin/rag/pipeline_runner.py)**: Orchestrates the ingestion of source texts into vector databases.

#### 🤖 [agent/](file:///Users/aditya1981/Documents/Vikram%20Sarabhai%20Digital%20Twin/agent)
Core execution graph and decision-making mechanisms.
- **[agent_graph.py](file:///Users/aditya1981/Documents/Vikram%20Sarabhai%20Digital%20Twin/agent/agent_graph.py)**: Defines the LangGraph StateGraph, managing routing logic, memory integration, persona prompts, and RAG injection nodes.
- **[intent_classifier.py](file:///Users/aditya1981/Documents/Vikram%20Sarabhai%20Digital%20Twin/agent/intent_classifier.py)**: Dynamically routes requests to conversational, planning, or mentoring states.
- **[tools.py](file:///Users/aditya1981/Documents/Vikram%20Sarabhai%20Digital%20Twin/agent/tools.py)**: Exposes workspace utility commands, retrieval actions, and metadata bindings.

#### 🛠️ [scripts/](file:///Users/aditya1981/Documents/Vikram%20Sarabhai%20Digital%20Twin/scripts)
Administration and diagnostics.
- **[run_system.py](file:///Users/aditya1981/Documents/Vikram%20Sarabhai%20Digital%20Twin/scripts/run_system.py)**: Wrapper script to configure environment variables and concurrently kick off backend servers.
- **[validate_system.py](file:///Users/aditya1981/Documents/Vikram%20Sarabhai%20Digital%20Twin/scripts/validate_system.py)**: Validates connectivity, tests endpoints, and checks file requirements.

## Corpus Collection

The quality of the Digital Twin is bounded by the quality of its knowledge base. Priority sources:

| Source | Priority |
|--------|----------|
| *Vikram Sarabhai: A Life* (Amrita Shah) | HIGH |
| ISRO official biography and speeches | HIGH |
| INCOSPAR founding documents (1962) | HIGH |
| Cosmic ray research papers (1940s–50s) | HIGH |
| IIM Ahmedabad founding papers | MEDIUM |
| Planning Commission contributions | MEDIUM |

## Testing

```bash
pytest tests/ -v
```

## License

This project is for educational and research purposes.
