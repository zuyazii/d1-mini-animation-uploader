"""FastAPI app that orchestrates uploads and PlatformIO builds."""

from __future__ import annotations

import io
import re
import uuid
import zipfile
from pathlib import Path
from typing import Iterable, List, Tuple

from fastapi import FastAPI, File, Form, HTTPException, Request, UploadFile
from fastapi.responses import HTMLResponse, Response
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel, Field

from . import config
from .builder import build_and_upload
from .converter import ImageValidationError, png_bytes_to_bitmap
from .state import FrameRecord, FrameStore


class FrameResponse(BaseModel):
    id: str
    name: str
    delay_ms: int
    order: int
    ascii_preview: List[str] = Field(default_factory=list)


class ReorderRequest(BaseModel):
    order: List[str]


class DelayUpdate(BaseModel):
    delay_ms: int = Field(gt=0, lt=60000)


class BuildResponse(BaseModel):
    header: str
    returncode: int
    stdout: str
    stderr: str


def create_app() -> FastAPI:
    config.ensure_dirs()
    
    # Check PlatformIO availability on startup
    from .platformio_manager import ensure_platformio, is_platformio_installed
    
    if not is_platformio_installed():
        print("PlatformIO not found. Attempting to install...")
        success, message, _ = ensure_platformio()
        if success:
            print(f"✓ {message}")
        else:
            print(f"⚠ Warning: {message}")
            print("You may need to install PlatformIO manually: pip install platformio")
    else:
        print("✓ PlatformIO is available")
    
    store = FrameStore(config.STATE_FILE)
    app = FastAPI(title="OLED Frame Builder", version="0.1.0")
    template_dir = Path(__file__).parent / "templates"
    template_dir.mkdir(parents=True, exist_ok=True)
    templates = Jinja2Templates(directory=str(template_dir))
    static_dir = Path(__file__).parent / "static"
    static_dir.mkdir(parents=True, exist_ok=True)
    app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

    def serialize(frames: Iterable[FrameRecord]) -> List[FrameResponse]:
        return [
            FrameResponse(
                id=frame.id,
                name=frame.name,
                delay_ms=frame.delay_ms,
                order=frame.order,
                ascii_preview=frame.ascii_preview,
            )
            for frame in frames
        ]

    @app.get("/", response_class=HTMLResponse)
    def index(request: Request) -> HTMLResponse:
        return templates.TemplateResponse(
            "index.html",
            {
                "request": request,
                "app_title": app.title,
                "app_config": {"defaultDelay": config.DEFAULT_DELAY_MS},
            },
        )

    @app.get("/favicon.ico")
    def favicon() -> Response:
        # Return empty 204 No Content to suppress favicon requests
        return Response(status_code=204)

    @app.get("/health")
    def health() -> dict:
        return {"status": "ok", "frames": len(store.list_frames())}

    @app.get("/frames", response_model=List[FrameResponse])
    def list_frames() -> List[FrameResponse]:
        return serialize(store.list_frames())

    @app.post("/upload", response_model=List[FrameResponse])
    async def upload_frames(
        files: List[UploadFile] = File(...),
        delay_ms: int = Form(config.DEFAULT_DELAY_MS),
    ) -> List[FrameResponse]:
        if not files:
            raise HTTPException(status_code=400, detail="No files provided.")
        
        if delay_ms <= 0:
            raise HTTPException(status_code=400, detail="Delay must be positive.")

        created: List[FrameRecord] = []
        for file in files:
            if not file.filename:
                continue
            
            try:
                payload = await file.read()
            except Exception as exc:
                raise HTTPException(status_code=400, detail=f"Failed to read upload {file.filename}: {exc}") from exc
            
            if not payload:
                continue
            if len(payload) > config.MAX_UPLOAD_BYTES:
                raise HTTPException(status_code=400, detail=f"Upload {file.filename} is too large.")

            try:
                members = _expand_upload(file.filename, payload)
            except ValueError as exc:
                raise HTTPException(status_code=400, detail=str(exc)) from exc

            for original_name, blob in members:
                try:
                    bitmap, ascii_rows = png_bytes_to_bitmap(blob)
                except ImageValidationError as exc:
                    raise HTTPException(status_code=400, detail=str(exc)) from exc

                frame_id = str(uuid.uuid4())
                safe_name = _safe_stem(original_name)
                source_path = _write_source(frame_id, safe_name, blob)
                record = store.add_frame(
                    frame_id=frame_id,
                    name=safe_name,
                    delay_ms=int(delay_ms),
                    source_path=source_path,
                    bitmap=bitmap,
                    ascii_preview=ascii_rows,
                )
                created.append(record)

        if not created:
            raise HTTPException(status_code=400, detail="No valid frames were created from the uploads.")
        return serialize(created)

    @app.patch("/frames/{frame_id}", response_model=FrameResponse)
    def update_frame_delay(frame_id: str, body: DelayUpdate) -> FrameResponse:
        try:
            record = store.update_delay(frame_id, body.delay_ms)
        except KeyError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        return serialize([record])[0]

    @app.post("/frames/delay-all", response_model=List[FrameResponse])
    def update_all_frame_delays(body: DelayUpdate) -> List[FrameResponse]:
        frames = store.update_all_delays(body.delay_ms)
        return serialize(frames)

    @app.post("/frames/reorder", response_model=List[FrameResponse])
    def reorder_frames(body: ReorderRequest) -> List[FrameResponse]:
        try:
            frames = store.reorder(body.order)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        return serialize(frames)

    @app.delete("/frames/{frame_id}")
    def delete_frame(frame_id: str) -> dict:
        try:
            store.delete(frame_id)
        except KeyError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        return {"status": "deleted"}

    @app.delete("/frames")
    def clear_all_frames() -> dict:
        store.clear_all()
        return {"status": "cleared"}

    @app.post("/build", response_model=BuildResponse)
    def build() -> BuildResponse:
        frames = store.list_frames()
        if not frames:
            raise HTTPException(status_code=400, detail="No frames to build.")
        result = build_and_upload(frames)
        return BuildResponse(**result)

    return app


# Create app instance for uvicorn
app = create_app()


def _expand_upload(filename: str, payload: bytes) -> List[Tuple[str, bytes]]:
    lowercase = filename.lower()
    if lowercase.endswith(".zip"):
        return _read_zip(payload)
    if lowercase.endswith(".png"):
        return [(filename, payload)]
    raise ValueError("Only .png images or .zip archives are supported.")


def _read_zip(payload: bytes) -> List[Tuple[str, bytes]]:
    members: List[Tuple[str, bytes]] = []
    with zipfile.ZipFile(io.BytesIO(payload)) as archive:
        for info in archive.infolist():
            if info.is_dir():
                continue
            if not info.filename.lower().endswith(".png"):
                continue
            data = archive.read(info.filename)
            members.append((Path(info.filename).name, data))
    if not members:
        raise ValueError("Zip archive does not contain PNG files.")
    return members


def _safe_stem(filename: str) -> str:
    stem = Path(filename).stem
    cleaned = re.sub(r"[^A-Za-z0-9_-]+", "_", stem)
    return cleaned or "frame"


def _write_source(frame_id: str, stem: str, blob: bytes) -> Path:
    config.SOURCES_DIR.mkdir(parents=True, exist_ok=True)
    path = config.SOURCES_DIR / f"{frame_id}_{stem}.png"
    path.write_bytes(blob)
    return path
