import io
from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.responses import JSONResponse

from registry.model_registry import registry

app = FastAPI(
    title="CS Forensics — ML Inference Service",
    description="Internal-only ML inference endpoint. Not exposed publicly.",
    version="1.0.0",
    docs_url=None,
    redoc_url=None,
)


@app.get("/health", include_in_schema=False)
async def health():
    return {"status": "ok", "service": "ml-inference"}


@app.post("/infer/image")
async def infer_image(file: UploadFile = File(...)):
    """
    Run CNN + ELA inference on an uploaded image.
    Returns: { is_tampered, confidence, ela_heatmap_bytes (base64) }
    """
    file_bytes = await file.read()
    if not file_bytes:
        raise HTTPException(status_code=400, detail="Empty file")

    try:
        model, version = registry.get_image_model()
        result = model.infer(file_bytes)
        result["model_version"] = version
        return JSONResponse(content=result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Inference failed: {str(e)}")


@app.post("/infer/video")
async def infer_video(file: UploadFile = File(...)):
    """
    Run CNN+LSTM temporal analysis on an uploaded video.
    Returns: { is_tampered, confidence, frame_results, tampered_frame_count }
    """
    file_bytes = await file.read()
    if not file_bytes:
        raise HTTPException(status_code=400, detail="Empty file")

    try:
        model, version = registry.get_video_model()
        result = model.infer(file_bytes)
        result["model_version"] = version
        return JSONResponse(content=result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Inference failed: {str(e)}")


@app.get("/models/active")
async def active_models():
    """Return which model versions are currently active."""
    from registry.model_registry import _MANIFEST_PATH
    import json
    with open(_MANIFEST_PATH) as f:
        manifest = json.load(f)
    return {
        "active_image_model": manifest["active_image_model"],
        "active_video_model": manifest["active_video_model"],
    }
