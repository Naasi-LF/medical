from __future__ import annotations

import json
import importlib
from pathlib import Path
from queue import Queue
from threading import Thread
from typing import Any, Iterator

from pydantic import BaseModel, Field

from gastric_agent.rag import GastricRAGAgent


BASE_DIR = Path(__file__).parent
WEB_DIR = BASE_DIR / "web"

fastapi_module = importlib.import_module("fastapi")
responses_module = importlib.import_module("fastapi.responses")
staticfiles_module = importlib.import_module("fastapi.staticfiles")

FastAPI = getattr(fastapi_module, "FastAPI")
FileResponse = getattr(responses_module, "FileResponse")
StreamingResponse = getattr(responses_module, "StreamingResponse")
StaticFiles = getattr(staticfiles_module, "StaticFiles")

app = FastAPI(title="Gastric Agent Web")
app.mount("/static", StaticFiles(directory=str(WEB_DIR)), name="static")


class ChatRequest(BaseModel):
    question: str = Field(min_length=1)
    think_mode: bool = True
    top_k: int = 5
    persist_dir: str = "data/vector_db"


@app.get("/")
def root() -> Any:
    return FileResponse(WEB_DIR / "index.html")


@app.post("/api/chat")
def chat(req: ChatRequest) -> dict[str, Any]:
    agent = GastricRAGAgent(persist_dir=req.persist_dir)
    resp = agent.answer(
        question=req.question,
        think_mode=req.think_mode,
        top_k=req.top_k,
    )
    return {
        "answer": resp.answer,
        "thinking": resp.thinking_trace,
        "sources": resp.sources,
        "references": resp.references,
    }


@app.post("/api/chat/stream")
def chat_stream(req: ChatRequest) -> Any:
    queue: Queue[dict[str, Any] | None] = Queue()

    def emit(event: str, data: Any) -> None:
        queue.put({"event": event, "data": data})

    def worker() -> None:
        try:
            agent = GastricRAGAgent(persist_dir=req.persist_dir)
            response = agent.answer(
                question=req.question,
                think_mode=req.think_mode,
                top_k=req.top_k,
                on_reasoning_token=lambda token: emit("reasoning", token),
                on_token=lambda token: emit("answer", token),
            )
            emit("references", response.references)
            emit("sources", response.sources)
            emit("done", True)
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
