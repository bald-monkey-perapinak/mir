import logging
from typing import Optional, Any

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.auth_deps import get_current_user, require_admin
from app.database import get_db
from app.models import Scenario, User
from app.training_engine import check_answer as engine_check

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/scenarios", tags=["scenarios"])

class ScenarioResponse(BaseModel):
    id: str
    document_id: str
    type: str
    title: str
    description: Optional[str]
    difficulty: int
    scenario_json: dict
    status: str

class CheckRequest(BaseModel):
    action_type: str                                                                 
    selected_option_index: Optional[int] = None
    blocks_order:          Optional[list[str]] = None
    free_text:             Optional[str] = None

class CheckResponse(BaseModel):
    correct:     bool
    score_delta: int
    explanation: Optional[str] = None
    consequence: Optional[str] = None
    visual_hint: Optional[str] = None
    detail:      Optional[Any] = None

@router.get("", response_model=list[ScenarioResponse])
async def list_scenarios(
    doc_id:     Optional[str] = Query(None),
    type:       Optional[str] = Query(None),
    difficulty: Optional[int] = Query(None),
    user: User = Depends(get_current_user),
    db:   AsyncSession = Depends(get_db),
):
    q = select(Scenario).where(Scenario.status == "active")
    if doc_id:
        q = q.where(Scenario.document_id == doc_id)
    if type:
        q = q.where(Scenario.type == type)
    if difficulty:
        q = q.where(Scenario.difficulty == difficulty)
    q = q.order_by(Scenario.created_at)

    result = await db.execute(q)
    return [_to_resp(s) for s in result.scalars().all()]

@router.get("/{scenario_id}", response_model=ScenarioResponse)
async def get_scenario(
    scenario_id: str,
    user: User = Depends(get_current_user),
    db:   AsyncSession = Depends(get_db),
):
    return _to_resp(await _get_or_404(scenario_id, db))

@router.patch("/{scenario_id}", response_model=ScenarioResponse)
async def update_scenario(
    scenario_id: str,
    body: dict,
    admin: User = Depends(require_admin),
    db:    AsyncSession = Depends(get_db),
):
    s = await _get_or_404(scenario_id, db)
    for key, val in body.items():
        if key in {"title", "description", "scenario_json", "difficulty", "status"}:
            setattr(s, key, val)
    await db.commit()
    await db.refresh(s)
    return _to_resp(s)

@router.post("/{scenario_id}/check", response_model=CheckResponse)
async def check_scenario_answer(
    scenario_id: str,
    body: CheckRequest,
    user: User = Depends(get_current_user),
    db:   AsyncSession = Depends(get_db),
):
\
\
\
       
    s = await _get_or_404(scenario_id, db)

    try:
        result = await engine_check(
            scenario_type=s.type,
            scenario_data=s.scenario_json,
            selected_option_index=body.selected_option_index,
            blocks_order=body.blocks_order,
            free_text=body.free_text,
        )
        return CheckResponse(**result)

    except Exception as exc:
        logger.error(
            f"Training engine error for scenario {scenario_id}: {exc}")
        raise HTTPException(503, f"Answer check failed: {exc}")

                                                                                

async def _get_or_404(scenario_id: str, db: AsyncSession) -> Scenario:
    result = await db.execute(select(Scenario).where(Scenario.id == scenario_id))
    s = result.scalar_one_or_none()
    if not s:
        raise HTTPException(404, "Scenario not found")
    return s

def _to_resp(s: Scenario) -> ScenarioResponse:
    return ScenarioResponse(
        id=s.id, document_id=s.document_id, type=s.type,
        title=s.title, description=s.description,
        difficulty=s.difficulty, scenario_json=s.scenario_json,
        status=s.status,
    )
