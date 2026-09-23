"""
Data Explorer router — serves CSV datasets as JSON for the browser Data Explorer page.
GET /api/v1/data-explorer/:dataset
Also triggers CSV regeneration on demand.
"""
import csv
import io
import logging
from pathlib import Path
from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import StreamingResponse
from ..core.dependencies import require_role
from ..schemas.common import ApiResponse

logger = logging.getLogger(__name__)
router = APIRouter()

# Resolve CSV directory relative to project root
_HERE = Path(__file__).resolve()
# backend/app/routers → backend/app → backend → project_root
_DATA_DIR = _HERE.parent.parent.parent.parent / "data" / "generated"

VALID_DATASETS = {
    "operators_profile",
    "machine_health_snapshot",
    "telemetry_correlated",
    "safety_events_enriched",
    "task_performance",
    "operator_machine_pairing",
    "near_miss_log",
    "carbon_passport",
}


def _read_csv(name: str) -> list[dict]:
    path = _DATA_DIR / f"{name}.csv"
    if not path.exists():
        return []
    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        return list(reader)


@router.get("/{dataset}")
async def get_dataset(
    dataset: str,
    _=Depends(require_role(["engineer", "admin", "supervisor", "safety_officer"])),
):
    if dataset not in VALID_DATASETS:
        raise HTTPException(404, f"Dataset '{dataset}' not found. Valid: {sorted(VALID_DATASETS)}")

    rows = _read_csv(dataset)

    # Summary stats
    summary: dict = {"total_rows": len(rows)}
    if rows and "safety_score" in rows[0]:
        scores = [float(r["safety_score"]) for r in rows if r.get("safety_score")]
        if scores:
            summary["avg_safety_score"] = round(sum(scores) / len(scores), 1)
    if rows and "co2_saved_kg" in rows[0]:
        co2 = [float(r["co2_saved_kg"]) for r in rows if r.get("co2_saved_kg")]
        if co2:
            summary["total_co2_saved_kg"] = round(sum(co2), 2)
    if rows and "overall_health" in rows[0]:
        healths = [float(r["overall_health"]) for r in rows if r.get("overall_health")]
        if healths:
            summary["avg_machine_health"] = round(sum(healths) / len(healths), 1)
    if rows and "anomaly_label" in rows[0]:
        summary["anomaly_count"] = sum(1 for r in rows if r.get("anomaly_label") == "UNUSUAL")
    if rows and "near_miss_self_corrected_count" in rows[0]:
        nm = [int(r["near_miss_self_corrected_count"]) for r in rows if r.get("near_miss_self_corrected_count")]
        summary["total_near_misses_self_corrected"] = sum(nm)

    return ApiResponse(data={"rows": rows, "summary": summary, "dataset": dataset})


@router.get("/{dataset}/download")
async def download_csv(
    dataset: str,
    _=Depends(require_role(["engineer", "admin", "supervisor", "safety_officer"])),
):
    """Stream the raw CSV file for download."""
    if dataset not in VALID_DATASETS:
        raise HTTPException(404, f"Dataset '{dataset}' not found.")
    path = _DATA_DIR / f"{dataset}.csv"
    if not path.exists():
        raise HTTPException(404, "CSV file not yet generated. POST /api/v1/data-explorer/regenerate first.")

    def iter_file():
        with open(path, "rb") as f:
            yield from f

    return StreamingResponse(
        iter_file(),
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="{dataset}.csv"'},
    )


@router.post("/regenerate")
async def regenerate_csvs(
    _=Depends(require_role(["engineer", "admin"])),
):
    """Re-run the CSV generator to refresh all datasets."""
    try:
        import sys
        import importlib.util
        gen_path = _DATA_DIR.parent / "generators" / "csv_generator.py"
        spec = importlib.util.spec_from_file_location("csv_generator", gen_path)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        counts = mod.write_csvs(_DATA_DIR, seed=42)
        return ApiResponse(data={"status": "ok", "rows_generated": counts})
    except Exception as e:
        logger.error(f"CSV regeneration failed: {e}")
        raise HTTPException(500, f"Regeneration failed: {str(e)}")
