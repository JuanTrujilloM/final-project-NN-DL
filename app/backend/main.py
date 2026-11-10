import asyncio
import json
import os
import sys
import uuid
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from pathlib import Path

from fastapi import FastAPI, HTTPException, Request
from fastapi.concurrency import run_in_threadpool
from fastapi.responses import FileResponse, StreamingResponse
from pydantic import BaseModel, Field

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from humaid.data.preprocess import clean_tweet

from .labels import GROUP_OF, GROUPS, LABEL_NAMES
from .registry import ModelRegistry

MODELS_ROOT = Path(os.environ.get("HUMAID_MODEL_DIR", ROOT / "models"))
DIST = ROOT / "app" / "frontend" / "dist"

registry = ModelRegistry(MODELS_ROOT)
posts = []
subscribers = set()


class NewPost(BaseModel):
    text: str = Field(..., min_length=1, max_length=280)
    author: str = Field(default="Tú", max_length=50)
    handle: str = Field(default="ciudadano_co", max_length=30)


class ActiveModel(BaseModel):
    model: str


def classification(model_id, probabilities):
    label = max(probabilities, key=probabilities.get)
    top = sorted(probabilities.items(), key=lambda item: item[1], reverse=True)[:3]
    return {
        "label": label,
        "label_name": LABEL_NAMES[label],
        "group": GROUP_OF[label],
        "confidence": round(probabilities[label], 4),
        "top": [{"label": k, "label_name": LABEL_NAMES[k], "p": round(v, 4)} for k, v in top],
        "model": model_id,
        "model_name": registry.models[model_id]["name"],
    }


def make_post(text, author, handle, created_at):
    return {"id": uuid.uuid4().hex[:12], "author": author, "handle": handle, "text": text,
            "clean_text": clean_tweet(text), "created_at": created_at.isoformat(), "classification": None}


def classify_posts(items, model_id=None):
    used, results = registry.classify([p["clean_text"] for p in items], model_id)
    for post, probabilities in zip(items, results):
        post["classification"] = classification(used, probabilities)


async def publish(event, data):
    for queue in list(subscribers):
        queue.put_nowait({"event": event, "data": data})


def meta():
    return {
        "labels": [{"id": k, "name": v, "group": GROUP_OF[k]} for k, v in LABEL_NAMES.items()],
        "groups": GROUPS,
        "models": registry.public_models(),
        "active_model": registry.active_id,
    }


# Loads the active model on startup so the first post does not wait for it.
@asynccontextmanager
async def lifespan(app):
    if registry.active_id:
        await run_in_threadpool(registry.get, registry.active_id)
    yield


app = FastAPI(title="AlertaNexo API", version="0.2.0", lifespan=lifespan)


@app.get("/api/meta")
def get_meta():
    return meta()


@app.get("/api/posts")
def get_posts():
    return posts


@app.post("/api/posts")
async def create_post(body: NewPost):
    post = make_post(body.text.strip(), body.author, body.handle, datetime.now(timezone.utc))
    try:
        await run_in_threadpool(classify_posts, [post])
    except RuntimeError as error:
        raise HTTPException(status_code=503, detail=str(error)) from error
    posts.insert(0, post)
    await publish("post_added", post)
    return post


@app.put("/api/active-model")
async def set_active_model(body: ActiveModel):
    try:
        await run_in_threadpool(registry.set_active, body.model)
    except KeyError as error:
        raise HTTPException(status_code=404, detail=f"Modelo no disponible: {body.model}") from error
    await publish("model_changed", {"active_model": registry.active_id})
    return meta()


# Classifies every post again with the active model, to compare models on the same feed.
@app.post("/api/reclassify")
async def reclassify():
    if posts:
        await run_in_threadpool(classify_posts, posts)
    await publish("posts_reset", posts)
    return posts


# Heartbeat so clients can tell a dead backend from a quiet one, even behind a proxy that keeps the connection open.
HEARTBEAT_SECONDS = 10


@app.get("/api/stream")
async def stream(request: Request):
    queue = asyncio.Queue()
    subscribers.add(queue)

    async def events():
        try:
            yield "retry: 2000\n\n"
            while not await request.is_disconnected():
                try:
                    message = await asyncio.wait_for(queue.get(), timeout=HEARTBEAT_SECONDS)
                except asyncio.TimeoutError:
                    yield "event: ping\ndata: {}\n\n"
                    continue
                yield f"event: {message['event']}\ndata: {json.dumps(message['data'], ensure_ascii=False)}\n\n"
        finally:
            subscribers.discard(queue)

    return StreamingResponse(events(), media_type="text/event-stream",
                             headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"})


# Built frontend (npm run build); any other path returns index.html so the client routes work.
@app.get("/{path:path}")
def frontend(path: str):
    if not DIST.is_dir():
        raise HTTPException(status_code=404, detail="Frontend sin compilar: corre npm run build en app/frontend")
    asset = (DIST / path).resolve()
    if path and DIST in asset.parents and asset.is_file():
        return FileResponse(asset)
    return FileResponse(DIST / "index.html")
