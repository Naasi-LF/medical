"""Memory routes: view/manage user graph memory."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status

from ..deps import get_current_user_id
from ..graph_memory import (
    delete_user_entity,
    delete_user_relation,
    extract_entities_from_text,
    get_user_memory,
    save_user_memory,
)
from ..models import MemoryEntityOut, MemoryInfoRequest, MemoryRelationOut

router = APIRouter(prefix="/api/memory", tags=["memory"])


@router.get("")
def get_memory(user_id: str = Depends(get_current_user_id)):
    memory = get_user_memory(user_id)
    return {
        "entities": [MemoryEntityOut(**e).model_dump() for e in memory["entities"]],
        "relations": [MemoryRelationOut(**r).model_dump() for r in memory["relations"]],
    }


@router.post("/extract")
def extract_and_save(
    req: MemoryInfoRequest,
    user_id: str = Depends(get_current_user_id),
):
    """Manually tell the agent personal info to remember."""
    extracted = extract_entities_from_text(req.text)
    stats = save_user_memory(user_id, extracted)
    return {
        "extracted": extracted,
        "saved": stats,
    }


@router.delete("/entity/{entity_id}")
def remove_entity(entity_id: str, user_id: str = Depends(get_current_user_id)):
    ok = delete_user_entity(user_id, entity_id)
    if not ok:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="未找到")
    return {"ok": True}


@router.delete("/relation/{relation_id}")
def remove_relation(relation_id: str, user_id: str = Depends(get_current_user_id)):
    ok = delete_user_relation(user_id, relation_id)
    if not ok:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="未找到")
    return {"ok": True}
