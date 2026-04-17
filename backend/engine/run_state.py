from __future__ import annotations

import json
from pathlib import Path
from uuid import uuid4

from schemas import RunInput, RunState


RUNS_DIR = Path(__file__).resolve().parent.parent / "data" / "runs"


def create_run(run_input: RunInput) -> RunState:
    return RunState(
        run_id=str(uuid4()),
        status="ready",
        input=run_input,
        confidence=0.5,
    )


def save_run_state(run_state: RunState) -> None:
    RUNS_DIR.mkdir(parents=True, exist_ok=True)
    path = RUNS_DIR / f"{run_state.run_id}.json"
    path.write_text(run_state.model_dump_json(indent=2), encoding="utf-8")


def load_run_state(run_id: str) -> RunState:
    path = RUNS_DIR / f"{run_id}.json"
    return RunState.model_validate_json(path.read_text(encoding="utf-8"))
