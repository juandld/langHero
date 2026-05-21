"""
Scenarios admin endpoints for managing game scenarios.
"""

import os
import asyncio
from fastapi import APIRouter, Request, Response, HTTPException
import config
from image import dalle as image_gen
import usage_log as usage
from security import request_guard, parse_json_body
from services.scenarios import (
    list_scenarios,
    reload_scenarios,
    get_scenario_by_id,
    list_scenario_versions,
    save_scenarios_version,
    activate_scenario_version,
)

router = APIRouter(prefix="/api/scenarios", tags=["scenarios"])


@router.get("")
async def api_list_scenarios():
    """List all scenarios."""
    return list_scenarios()


@router.get("/{scenario_id}")
async def api_get_scenario(scenario_id: int):
    """Get a single scenario by ID."""
    scenario = get_scenario_by_id(scenario_id)
    if not scenario:
        raise HTTPException(status_code=404, detail="scenario_not_found")
    return scenario


@router.post("/{scenario_id}/generate-image")
async def generate_scenario_image(scenario_id: int, request: Request):
    """Generate an AI scene image for a scenario via DALL-E 3.

    Returns {url, cached, cache_key}.
    """
    await request_guard(
        request,
        rate_bucket="image_gen",
        rate_limit_per_min=int(getattr(config, "RATE_LIMIT_IMPORT_PER_MIN", 10)),
    )

    scenario = get_scenario_by_id(scenario_id)
    if not scenario:
        raise HTTPException(status_code=404, detail="scenario_not_found")

    body = await parse_json_body(request)

    force = bool((body or {}).get("force", False))

    try:
        result = await asyncio.to_thread(image_gen.generate_scene_image, scenario, force=force)
        try:
            usage.log_usage(
                event=("image_cache_hit" if result.get("cached") else "image_generate"),
                provider="openai",
                model="dall-e-3",
                key_label=usage.OPENAI_LABEL,
                status="success",
            )
        except Exception:
            pass
        return result
    except Exception as e:
        try:
            usage.log_usage(
                event="image_generate",
                provider="openai",
                model="dall-e-3",
                key_label=usage.OPENAI_LABEL,
                status="error",
            )
        except Exception:
            pass
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{scenario_id}/image")
async def get_scenario_image(scenario_id: int):
    """Check if a cached image exists for a scenario.

    Returns {url, exists} or {exists: false}.
    """
    scenario = get_scenario_by_id(scenario_id)
    if not scenario:
        raise HTTPException(status_code=404, detail="scenario_not_found")

    cached_url = image_gen.get_cached_image(scenario)
    if cached_url:
        return {"url": cached_url, "exists": True}
    return {"exists": False}


@router.post("/import")
async def api_import_scenarios(request: Request):
    """Replace scenarios with provided list. Body: {"scenarios": [...]}"""
    try:
        await request_guard(
            request,
            admin_flag=bool(config.REQUIRE_ADMIN_FOR_IMPORT),
            auth_flag=bool(config.REQUIRE_AUTH_FOR_IMPORT),
            rate_bucket="scenarios_import",
        )
        body = await request.json()
        scenarios = (body or {}).get("scenarios")
        if not isinstance(scenarios, list):
            return Response(status_code=400)
        reload_scenarios(scenarios)
        return {"status": "ok", "count": len(scenarios)}
    except Exception as e:
        return {"error": str(e)}
