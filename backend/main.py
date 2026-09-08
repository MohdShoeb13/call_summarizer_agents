from concurrent.futures import ThreadPoolExecutor
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from pathlib import Path
from threading import BoundedSemaphore
from uuid import uuid4

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from backend.agents.intake_agent import MAX_BYTES, intake
from backend.agents.routing_agent import process
from backend.config import settings
from backend.models import CallResult, Health, SampleInfo
from backend.provider import OpenAIProvider
from backend.samples import ReplayProvider, samples
from backend.store import Store


@asynccontextmanager
async def lifespan(app):
    app.state.store = Store(settings.database_path)
    app.state.store.interrupt_pending()
    app.state.executor = ThreadPoolExecutor(max_workers=settings.workers)
    app.state.capacity = BoundedSemaphore(settings.workers + 8)
    yield
    app.state.executor.shutdown(wait=True)


app = FastAPI(title="Resonant Call Intelligence", version="0.1.0", lifespan=lifespan)


@app.get("/api/health", response_model=Health)
def health():
    return Health(ready=bool(settings.openai_api_key))


@app.get("/api/samples", response_model=list[SampleInfo])
def list_samples():
    return [SampleInfo(id=s["id"], title=s["title"], scenario=s["scenario"]) for s in samples()]


@app.get("/api/calls", response_model=list[CallResult])
def list_calls():
    return app.state.store.list()


@app.get("/api/calls/{call_id}", response_model=CallResult)
def get_call(call_id: str):
    result = app.state.store.get(call_id)
    if not result:
        raise HTTPException(404, "Call not found.")
    return result


@app.get("/api/calls/{call_id}/export", response_model=CallResult)
def export_call(call_id: str):
    call = get_call(call_id)
    return JSONResponse(call.model_dump(), headers={"Content-Disposition": f'attachment; filename="resonant-{call.id}.json"'})


@app.post("/api/calls", response_model=CallResult, status_code=202)
async def create_call(file: UploadFile | None = File(None), sample_id: str | None = Form(None), demo: bool = Form(False), simulate_failure: bool = Form(False)):
    if bool(file) == bool(sample_id):
        raise HTTPException(422, "Choose one file or one sample.")
    provider = OpenAIProvider(settings)
    if sample_id:
        sample = next((s for s in samples() if s["id"] == sample_id), None)
        if not sample:
            raise HTTPException(404, "Sample not found.")
        filename, content = sample["id"] + ".txt", sample["transcript"].encode()
        title = sample["title"]
        if demo:
            provider = ReplayProvider(sample, simulate_failure)
    else:
        if demo or simulate_failure:
            raise HTTPException(422, "Replay and failure simulation are available only for curated samples.")
        try:
            content = await file.read(MAX_BYTES + 1)
            filename = (file.filename or "upload").replace("\\", "/").split("/")[-1]
        finally:
            await file.close()
        title = Path(filename).stem[:100]
    if simulate_failure and not demo:
        raise HTTPException(422, "Failure simulation requires sample replay mode.")
    try:
        intake(filename, content)
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from exc
    if not demo and not settings.openai_api_key:
        raise HTTPException(503, "Add OPENAI_API_KEY to the backend .env and restart. Sample replay is available without a key.")
    if not app.state.capacity.acquire(blocking=False):
        raise HTTPException(429, "Processing queue is full. Try again after an active call finishes.")
    call = CallResult(id=str(uuid4()), title=title, created_at=datetime.now(timezone.utc).isoformat(), status="queued", stage="intake", demo=demo)

    def run():
        try:
            process(call, filename, content, provider, app.state.store)
        finally:
            app.state.capacity.release()

    try:
        app.state.store.save(call)
        # Snapshot the accepted response before a worker mutates the result.
        accepted = call.model_copy(deep=True)
        app.state.executor.submit(run)
    except Exception:
        app.state.capacity.release()
        raise
    return accepted


DIST = Path(__file__).resolve().parents[1] / "frontend" / "dist"
if DIST.exists():
    app.mount("/assets", StaticFiles(directory=DIST / "assets"), name="assets")

    @app.get("/", include_in_schema=False)
    @app.get("/workspace", include_in_schema=False)
    def frontend():
        return FileResponse(DIST / "index.html")
