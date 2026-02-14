"""Chat routes: conversations + streaming Q&A with memory."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from queue import Queue
from threading import Thread
from typing import Any, Iterator

from bson import ObjectId
from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse

from gastric_agent.rag import GastricRAGAgent

from ..database import conversations_col, messages_col
from ..deps import get_current_user_id
from ..graph_memory import (
    build_memory_context,
    extract_entities_from_text,
    save_user_memory,
)
from ..models import ChatRequest, ConversationOut, MessageOut

router = APIRouter(prefix="/api/chat", tags=["chat"])

PERSIST_DIR = "data/vector_db"


# ---------- Conversation CRUD ----------


@router.get("/conversations", response_model=list[ConversationOut])
def list_conversations(user_id: str = Depends(get_current_user_id)):
    col = conversations_col()
    docs = col.find({"user_id": user_id}).sort("updated_at", -1).limit(50)
    result = []
    for doc in docs:
        result.append(
            ConversationOut(
                id=str(doc["_id"]),
                title=doc.get("title", "新对话"),
                updated_at=doc.get("updated_at", ""),
            )
        )
    return result


@router.post("/conversations")
def create_conversation(user_id: str = Depends(get_current_user_id)):
    now = datetime.now(timezone.utc).isoformat()
    doc = {
        "user_id": user_id,
        "title": "新对话",
        "created_at": now,
        "updated_at": now,
    }
    result = conversations_col().insert_one(doc)
    return {"id": str(result.inserted_id), "title": "新对话"}


@router.delete("/conversations/{conv_id}")
def delete_conversation(conv_id: str, user_id: str = Depends(get_current_user_id)):
    conversations_col().delete_one({"_id": ObjectId(conv_id), "user_id": user_id})
    messages_col().delete_many({"conversation_id": conv_id})
    return {"ok": True}


@router.get("/conversations/{conv_id}/messages", response_model=list[MessageOut])
def get_messages(conv_id: str, user_id: str = Depends(get_current_user_id)):
    # Verify ownership
    conv = conversations_col().find_one({"_id": ObjectId(conv_id), "user_id": user_id})
    if not conv:
        return []

    docs = messages_col().find({"conversation_id": conv_id}).sort("created_at", 1)
    return [
        MessageOut(
            role=d["role"],
            content=d["content"],
            thinking=d.get("thinking", ""),
            sources=d.get("sources", []),
            references=d.get("references", []),
            created_at=d.get("created_at", ""),
        )
        for d in docs
    ]


# ---------- Chat stream ----------


@router.post("/stream")
def chat_stream(req: ChatRequest, user_id: str = Depends(get_current_user_id)):
    conv_id = req.conversation_id

    # Auto-create conversation if none specified
    if not conv_id:
        now = datetime.now(timezone.utc).isoformat()
        doc = {
            "user_id": user_id,
            "title": req.question[:20] + ("..." if len(req.question) > 20 else ""),
            "created_at": now,
            "updated_at": now,
        }
        result = conversations_col().insert_one(doc)
        conv_id = str(result.inserted_id)

    # Save user message
    now = datetime.now(timezone.utc).isoformat()
    messages_col().insert_one(
        {
            "conversation_id": conv_id,
            "role": "user",
            "content": req.question,
            "created_at": now,
        }
    )

    # Update conversation title if first message
    msg_count = messages_col().count_documents({"conversation_id": conv_id})
    if msg_count == 1:
        title = req.question[:20] + ("..." if len(req.question) > 20 else "")
        conversations_col().update_one(
            {"_id": ObjectId(conv_id)},
            {"$set": {"title": title}},
        )

    queue: Queue[dict[str, Any] | None] = Queue()

    def emit(event: str, data: Any) -> None:
        queue.put({"event": event, "data": data})

    def worker() -> None:
        try:
            # Extract entities from user message (background)
            try:
                extracted = extract_entities_from_text(req.question)
                if extracted["entities"] or extracted["relations"]:
                    save_user_memory(user_id, extracted)
                    emit(
                        "memory_update",
                        {
                            "entities": len(extracted["entities"]),
                            "relations": len(extracted["relations"]),
                        },
                    )
            except Exception:
                pass  # Non-critical: don't break chat if extraction fails

            # Build personalized context from graph memory
            memory_context = build_memory_context(user_id)

            agent = GastricRAGAgent(persist_dir=PERSIST_DIR)
            response = agent.answer(
                question=req.question,
                think_mode=req.think_mode,
                top_k=req.top_k,
                on_reasoning_token=lambda token: emit("reasoning", token),
                on_token=lambda token: emit("answer", token),
                memory_context=memory_context,
            )

            emit("references", response.references)
            emit("sources", response.sources)
            emit("answer_final", response.answer)
            emit("conversation_id", conv_id)
            emit("done", True)

            # Save assistant message
            messages_col().insert_one(
                {
                    "conversation_id": conv_id,
                    "role": "assistant",
                    "content": response.answer,
                    "thinking": response.thinking_trace,
                    "sources": response.sources,
                    "references": response.references,
                    "created_at": datetime.now(timezone.utc).isoformat(),
                }
            )

            # Update conversation timestamp
            conversations_col().update_one(
                {"_id": ObjectId(conv_id)},
                {"$set": {"updated_at": datetime.now(timezone.utc).isoformat()}},
            )

        except Exception as exc:
            emit("error", str(exc))
        finally:
            queue.put(None)

    Thread(target=worker, daemon=True).start()

    def stream() -> Iterator[str]:
        while True:
            item = queue.get()
            if item is None:
                break
            yield json.dumps(item, ensure_ascii=False) + "\n"

    return StreamingResponse(stream(), media_type="application/x-ndjson")
