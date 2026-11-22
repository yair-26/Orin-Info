"""FastAPI entry point (T-01). NOT TESTED YET: written in an environment without network."""
from fastapi import FastAPI

app = FastAPI(title="ORIN INFO")


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}
