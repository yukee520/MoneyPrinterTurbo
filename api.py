from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import FileResponse, JSONResponse
import subprocess
import os
import time
from typing import Optional
from pydantic import BaseModel

app = FastAPI()

# Configuration
OUTPUT_DIR = "/tmp/outputs"
os.makedirs(OUTPUT_DIR, exist_ok=True)

class VideoRequest(BaseModel):
    text: str = "To the moon!"
    duration: int = 5  # seconds
    width: int = 1280
    height: int = 720
    bg_color: str = "#121212"
    text_color: str = "white"
    font_size: int = 60

@app.get("/")
async def root():
    return JSONResponse(
        content={
            "message": "Enhanced Money Printer Turbo API",
            "endpoints": {
                "generate": "POST /generate",
                "download": "GET /download/{filename}"
            },
            "defaults": {
                "duration": 5,
                "resolution": "1280x720",
                "colors": {"background": "#121212", "text": "white"}
            }
        }
    )

@app.post("/generate")
async def generate_video(request: Request):
    """Generate high quality video with custom text"""
    try:
        # Parse request
        data = await request.json()
        req = VideoRequest(**data)
        
        # Create filename
        timestamp = int(time.time())
        filename = f"video_{timestamp}.mp4"
        output_path = f"{OUTPUT_DIR}/{filename}"
        
        # Enhanced FFmpeg command
        cmd = [
            "ffmpeg",
            "-f", "lavfi",
            "-i", f"color=c={req.bg_color}:s={req.width}x{req.height}:d={req.duration}:r=30",
            "-vf", f"drawtext=text='{req.text}':"
                   f"fontsize={req.font_size}:"
                   f"fontcolor={req.text_color}:"
                   "x=(w-text_w)/2:y=(h-text_h)/2:"
                   "fontfile=/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
            "-c:v", "libx264",
            "-preset", "fast",
            "-crf", "18",  # Quality level (0-51, lower is better)
            "-pix_fmt", "yuv420p",
            "-movflags", "+faststart",  # For web streaming
            "-y",  # Overwrite without prompt
            output_path
        ]
        
        # Execute with timing
        start_time = time.time()
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True
        )
        generation_time = round(time.time() - start_time, 2)
        
        if result.returncode != 0:
            raise Exception(f"FFmpeg Error: {result.stderr}")
            
        # Get file stats
        file_stats = os.stat(output_path)
        file_size = file_stats.st_size / (1024 * 1024)  # in MB
        
        return JSONResponse(
            content={
                "status": "success",
                "filename": filename,
                "download_url": f"/download/{filename}",
                "details": {
                    "resolution": f"{req.width}x{req.height}",
                    "duration_sec": req.duration,
                    "file_size_mb": round(file_size, 2),
                    "generation_time_sec": generation_time,
                    "bitrate": f"{round(file_size * 8 / req.duration, 2)} Mbps"
                }
            }
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={
                "error": str(e),
                "solution": "Check valid parameters and server logs"
            }
        )

@app.get("/download/{filename}")
async def download_video(filename: str):
    """Download video with proper headers for all clients"""
    file_path = f"{OUTPUT_DIR}/{filename}"
    if os.path.exists(file_path):
        return FileResponse(
            file_path,
            media_type="video/mp4",
            headers={
                "Content-Disposition": f"attachment; filename={filename}",
                "Content-Length": str(os.path.getsize(file_path)),
                "Cache-Control": "no-store"
            }
        )
    raise HTTPException(
        status_code=404,
        detail={
            "error": "File not found",
            "possible_reasons": [
                "File expired (temp files are auto-cleaned)",
                "Invalid filename",
                "Never generated successfully"
            ]
        }
    )

# Background cleanup task would go here (optional)
