"""RAG engineer copilot router — P1 feature."""
from fastapi import APIRouter, Depends
from ..core.dependencies import require_role
from ..schemas.common import ApiResponse

router = APIRouter()

_history: list[dict] = []


@router.post("/query")
async def copilot_query(
    body: dict,
    _=Depends(require_role(["engineer", "admin"])),
):
    question = body.get("question", "")
    context_filter = body.get("context_filter", {})

    # Try to use RAG service if available
    try:
        import sys, os
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../../../rag"))
        from rag.retrieval.rag_service import get_rag_response
        result = await get_rag_response(question, context_filter)
    except Exception:
        result = _mock_response(question, context_filter)

    _history.append({"role": "user", "content": question})
    _history.append({"role": "assistant", "content": result["answer"]})
    return ApiResponse(data=result)


@router.get("/history")
async def get_history(_=Depends(require_role(["engineer", "admin"]))):
    return ApiResponse(data=_history)


@router.delete("/history")
async def clear_history(_=Depends(require_role(["engineer", "admin"]))):
    _history.clear()
    return ApiResponse(data={"cleared": True})


def _mock_response(question: str, context_filter: dict) -> dict:
    q_lower = question.lower()
    if "hydraulic" in q_lower:
        answer = ("Based on the machine manual, hydraulic pressure outside the 200–300 bar operating range "
                  "indicates a potential issue with the hydraulic pump, filter blockage, or fluid leak. "
                  "Recommended action: Reduce operating load, inspect hydraulic fluid level and filter condition. "
                  "Fault code E-HYD-042 specifically indicates filter differential pressure above threshold.")
        sources = [{"document": "excavator_manual.md", "chunk": "Hydraulic System — Fault Codes", "relevance": 0.92}]
    elif "maintenance" in q_lower or "service" in q_lower:
        answer = ("Per the maintenance schedule, the CAT 390F requires an oil and filter change every 500 engine hours. "
                  "Hydraulic filter replacement is due every 1000 hours. Current machine data suggests service is approaching. "
                  "Contact the maintenance team to schedule downtime.")
        sources = [{"document": "maintenance_schedule.md", "chunk": "Scheduled Maintenance Intervals", "relevance": 0.89}]
    elif "proximity" in q_lower or "person" in q_lower:
        answer = ("Site safety guidelines require all personnel to maintain a minimum 10m distance from operating excavators. "
                  "Critical proximity threshold is 5m — machine should be halted immediately. "
                  "Today's proximity incidents show a pattern in Zone A1. Consider reviewing worker access controls for that zone.")
        sources = [{"document": "safety_guidelines.md", "chunk": "Proximity Safety Rules", "relevance": 0.95}]
    elif "operator" in q_lower and "training" in q_lower:
        answer = ("Based on current training records, 3 operators have pending mandatory safety modules. "
                  "OP1004 has a proximity safety module overdue (3 proximity events in the last 7 days). "
                  "OP1009's CAT certification expires in 8 days — renewal required before next machine authorization.")
        sources = [{"document": "operator_training_guide.md", "chunk": "Certification Requirements", "relevance": 0.88}]
    else:
        answer = (f"Based on the available documentation and site data, here is what I found relevant to your query: '{question}'. "
                  "For detailed technical specifications, refer to the machine manual. For safety queries, refer to site safety guidelines. "
                  "Note: This is a demo response from synthetic documentation — not validated CAT technical content.")
        sources = [{"document": "faq.md", "chunk": "General Queries", "relevance": 0.65}]

    return {
        "answer": answer,
        "sources": sources,
        "disclaimer": "Responses generated from synthetic demo documents. Not validated CAT documentation.",
        "mock": True,
    }
