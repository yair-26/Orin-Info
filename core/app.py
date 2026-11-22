"""FastAPI app: /health plus read-only /calls, /calls/{id}, /summary (api-contracts v0.1).

Data source: JSONL turn log at $ORIN_LOG_PATH (default: admin/mock-data/sample_log.jsonl, which is
FICTITIOUS demo data). No database yet (D-004 pending). NOT TESTED with FastAPI in the authoring
environment (no network); the aggregation logic itself is covered in tests/test_reporting.py.
"""
import os
from pathlib import Path

from fastapi import FastAPI, HTTPException, Query

from core.reporting import call_detail, call_list, summary
from core.turnlog import read_log

DEFAULT_LOG = Path(__file__).resolve().parent.parent / "admin" / "mock-data" / "sample_log.jsonl"

app = FastAPI(title="ORIN INFO (staging, demo data)")


def _lines() -> list[dict]:
    return read_log(os.environ.get("ORIN_LOG_PATH", DEFAULT_LOG))


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.get("/calls")
def get_calls(limit: int = Query(50, ge=1, le=500), offset: int = Query(0, ge=0),
              from_: str | None = Query(None, alias="from"), to: str | None = None,
              status: str | None = None) -> list[dict]:
    return call_list(_lines(), status=status, from_=from_, to=to, limit=limit, offset=offset)


@app.get("/calls/{call_id}")
def get_call(call_id: str) -> dict:
    detail = call_detail(_lines(), call_id)
    if detail is None:
        raise HTTPException(status_code=404, detail="call not found")
    return detail


@app.get("/summary")
def get_summary(from_: str | None = Query(None, alias="from"), to: str | None = None) -> dict:
    return summary(_lines(), from_=from_, to=to)
