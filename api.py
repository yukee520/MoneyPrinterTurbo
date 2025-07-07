from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import FileResponse, JSONResponse
import subprocess
import os
import time
from typing import Optional
from pydantic import BaseModel

app = FastAPI()

# Configuration - using Render's writable /tmp directory
OUTPUT_DIR = "/tmp/outputs"
os.makedirs(OUTPUT_DIR, exist_ok=True)

class VideoRequest(BaseModel):
    text: str = "To the moon!"
    duration: int = 5
    width: int = 1280
    height: int = 720
    bg_color: str = "#121212"
    text_color: str = "white"
    font_size: int = 60

@app.get("/")
async def root():
    return {
        "status": "ready",
        "endpoints": {
            "generate": "POST /generate",
            "download": "GET /download/{filename}"
        }
    }

@app.post("/generate")
async def generate_video(request: Request):
    try:
        data = await request.json()
        req = VideoRequest(**data)
        
        filename = f"video_{int(time.time())}.mp4"
        output_path = f"{OUTPUT_DIR}/{filename}"
        
        # FFmpeg command using Render's built-in ffmpeg
        cmd = [
            "ffmpeg",
            "-f", "lavfi",
            "-i", f"color=c={req.bg_color}:s={req.width}x{req.height}:d={req.duration}",
            "-vf", f"drawtext=text='{req.text}':fontsize={req.font_size}:fontcolor={req.text_color}:x=(w-text_w)/2:y=(h-text_h)/2",
            "-c:v", "libx264",
            "-preset", "fast",
            "-crf", "23",
            "-y",
            output_path
        ]
        
        start = time.time()
        result = subprocess.run(cmd, capture_output=True, text=True)
        gen_time = round(time.time() - start, 2)
        
        if result.returncode != 0:
            raise Exception(result.stderr)
            
        return {
            "status": "success",
            "filename": filename,
            "download_url": f"/download/{filename}",
            "details": {
                "generation_time": f"{gen_time}s",
                "resolution": f"{req.width}x{req.height}"
            }
        }
        
    except Exception as e:
        raise HTTPException(500, detail=str(e))

@app.get("/download/{filename}")
async def download_video(filename: str):
    file_path = f"{OUTPUT_DIR}/{filename}"
    if os.path.exists(file_path):
        return FileResponse(
            file_path,
            media_type="video/mp4",
            filename=filename,
            headers={"Cache-Control": "no-store"}
        )
    raise HTTPException(404, "File not found")
