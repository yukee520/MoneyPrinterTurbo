from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from pathlib import Path
import uuid
import os
from moviepy.editor import TextClip, concatenate_videoclips

app = FastAPI()

# Serve the /output folder as static files
app.mount("/files", StaticFiles(directory="output"), name="output")

# Define input structure
class PromptRequest(BaseModel):
    prompt: str

@app.get("/")
async def root():
    return {"message": "Money Printer Turbo is live. POST to /generate"}

@app.post("/generate")
async def generate(request: PromptRequest):
    prompt_text = request.prompt.strip()
    if not prompt_text:
        return JSONResponse(content={"error": "Prompt is empty"}, status_code=400)

    # Unique filename
    filename = f"{uuid.uuid4().hex}.mp4"
    output_path = Path("output") / filename
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Generate simple text clip
    try:
        clip = TextClip(prompt_text, fontsize=70, color='white', bg_color='black', size=(720, 1280)).set_duration(5)
        clip.write_videofile(str(output_path), fps=24, codec='libx264', audio=False)
    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=500)

    return {"status": "video generated", "file": filename}

@app.get("/ping")
async def ping():
    return {"status": "OK"}

@app.get("/files/{file_name}")
async def serve_file(file_name: str):
    file_path = Path("output") / file_name
    if not file_path.exists():
        return JSONResponse(status_code=404, content={"detail": "Not Found"})
    return FileResponse(str(file_path), media_type="video/mp4", filename=file_name)
