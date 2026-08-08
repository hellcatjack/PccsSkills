from __future__ import annotations

import importlib
import sys
from pathlib import Path


SKILL_DIR = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = SKILL_DIR / "scripts"
PROJECT_ROOT = SKILL_DIR.parents[2]

if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))


def load_pipeline_module(name: str):
    try:
        return importlib.import_module(f"subtitle_pipeline.{name}")
    except ModuleNotFoundError as error:
        if error.name in {"subtitle_pipeline", f"subtitle_pipeline.{name}"}:
            return None
        raise
