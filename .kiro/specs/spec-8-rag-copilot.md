# Spec 8 — RAG Engineer Copilot

## Status: P1 — Build if time permits after P0

---

## Requirements

### REQ-8.1 RAG architecture
Engineer-only chatbot that answers from:
- Simulated machine manuals (synthetic documents)
- Safety guidelines
- Maintenance documentation
- Internal FAQ

Pipeline:
```
Documents → chunking → embeddings → ChromaDB
                                         ↓
User query → embed query → retrieve top-k chunks
                                         ↓
                               LLM (configurable) → answer + sources
```

### REQ-8.2 Document set (synthetic, for demo)
Create small synthetic documents in `rag/documents/`:
- `excavator_manual.md` — engine specs, fault codes, operating procedures
- `safety_guidelines.md` — proximity rules, seatbelt policy, zone definitions
- `maintenance_schedule.md` — service intervals, maintenance types
- `fault_codes.md` — list of fault codes with descriptions and recommended actions
- `operator_training_guide.md` — certification requirements, training modules
- `faq.md` — common questions and answers

All synthetic — not copied from real CAT documentation.

### REQ-8.3 LLM provider config
```
LLM_PROVIDER=mock     # always works, returns canned responses
LLM_PROVIDER=openai   # uses OPENAI_API_KEY env var
LLM_PROVIDER=local    # uses local Ollama endpoint
```
Mock provider must produce realistic-looking responses for the demo.

### REQ-8.4 Copilot API
```
POST /copilot/query
  body: { "question": str, "context_filter": { "machine_id": str? } }
  response: {
    "answer": str,
    "sources": [{ "document": str, "chunk": str, "relevance": float }],
    "structured_data": { ... }  # if query matches structured DB data
  }

GET /copilot/history         engineer only — conversation history
DELETE /copilot/history      clear conversation
```

### REQ-8.5 Hybrid retrieval
For certain query patterns, supplement RAG with structured DB queries:
- "Why is EXC001 showing a hydraulic warning?" → fetch machine health + recent faults from DB
- "Which operators have pending training?" → query training_recommendations table
- "Show today's incidents" → query incidents table

Detected via keyword matching + regex, not full NLP for MVP.

### REQ-8.6 Copilot page (`/copilot`)
- Engineer/admin only
- Chat interface: message history + input box
- Sources panel: shows retrieved document chunks for last answer
- Example queries shown as quick-start chips
- Disclaimer: "Responses are generated from synthetic demo documents. Not validated CAT documentation."

---

## Design

### RAG service
```python
# rag/retrieval/rag_service.py
class RAGService:
    def __init__(self, chroma_client, embedder, llm_provider):
        ...

    async def query(self, question: str, context_filter: dict) -> RAGResponse:
        # 1. Detect if structured DB query needed
        # 2. Embed question
        # 3. Retrieve top-5 chunks from ChromaDB
        # 4. Build prompt with chunks + optional DB context
        # 5. Call LLM
        # 6. Return answer + sources
```

### Mock LLM responses
`rag/retrieval/mock_llm.py` — returns pre-written answers for common demo queries:
- "hydraulic warning" → explains hydraulic pressure threshold, recommends check
- "maintenance due" → shows next service schedule
- "proximity incidents" → summarizes today's proximity events
- Generic fallback: "Based on the documentation, [relevant chunk summary]..."

### Document indexing
`rag/embeddings/index_documents.py` — run once to build ChromaDB index:
```
python rag/embeddings/index_documents.py
```

---

## Tasks

- [ ] Create synthetic RAG documents (6 markdown files)
- [ ] Create rag/embeddings/index_documents.py
- [ ] Create rag/retrieval/rag_service.py
- [ ] Create rag/retrieval/mock_llm.py
- [ ] Create rag/retrieval/openai_llm.py (if time)
- [ ] Create structured query detector
- [ ] Create backend/app/routers/copilot.py
- [ ] Create backend/app/services/copilot_service.py
- [ ] Create frontend copilot page (/copilot)
- [ ] Create chat message component
- [ ] Create sources panel component
- [ ] Add example query chips
- [ ] Add disclaimer banner
