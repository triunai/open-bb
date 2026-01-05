"""
OpenBB Widgets Routes

Endpoints for OpenBB Workspace integration:
- /widgets.json - Widget definitions
- /apps.json - App layouts
"""

import json
from pathlib import Path

from fastapi import APIRouter
from fastapi.responses import JSONResponse


router = APIRouter(tags=["OpenBB"])


# Load static JSON files
_OPENBB_DIR = Path(__file__).parent.parent.parent / "openbb"


def _load_json(filename: str) -> dict:
    """Load a JSON file from the openbb directory."""
    filepath = _OPENBB_DIR / filename
    if filepath.exists():
        return json.loads(filepath.read_text())
    return {}


@router.get("/widgets.json")
async def get_widgets() -> JSONResponse:
    """
    Widget definitions for OpenBB Workspace.
    
    Returns:
        widgets.json content
    """
    content = _load_json("widgets.json")
    return JSONResponse(content=content)


@router.get("/apps.json")
async def get_apps() -> JSONResponse:
    """
    App layouts for OpenBB Workspace.
    
    Returns:
        apps.json content
    """
    content = _load_json("apps.json")
    return JSONResponse(content=content)
