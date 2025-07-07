from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse, FileResponse
import subprocess
import os
import time
import logging
from pydantic import BaseModel

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

# Configuration
OUTPUT_DIR = "/tmp/outputs"
os.makedirs(OUTPUT_DIR, exist_ok=True)

class VideoRequest(BaseModel):
    text: str = "To the moon!"
    duration: int = 5
    width: int = 1280
    height: int = 720
    bg_color: str = "#121212"
    text_color: str = "white"

@app.get("/")
async def health_check():
    return {"status": "ready", "message": "Money Printer Turbo API"}

@app.post("/generate")
async def generate_video(request: Request):
    """Generate video with progress tracking"""
    start_time = time.time()
    try:
        # Parse request
        data = await request.json()
        req = VideoRequest(**data)
        logger.info(f"Generation request: {data}")
        
        # Create output file
        filename = f"video_{int(time.time())}.mp4"
        output_path = f"{OUTPUT_DIR}/{filename}"
        
        # FFmpeg command (Render.com has ffmpeg pre-installed)
        cmd = [
            "ffmpeg",
            "-f", "lavfi",
            "-i", f"color=c={req.bg_color}:s={req.width}x{req.height}:d={req.duration}",
            "-vf", f"drawtext=text='{req.text}':fontcolor={req.text_color}:x=(w-text_w)/2:y=(h-text_h)/2",
            "-c:v", "libx264",
            "-preset", "fast",
            "-crf", "23",
            "-y",  # Overwrite if exists
            output_path
        ]
        
        logger.info(f"Executing: {' '.join(cmd)}")
        
        # Run FFmpeg with timeout
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=30  # 30 second timeout
            )
        except subprocess.TimeoutExpired:
            logger.error("FFmpeg timed out")
            raise HTTPException(500, "Video generation timed out")
        
        if result.returncode != 0:
            logger.error(f"FFmpeg failed: {result.stderr}")
            raise HTTPException(500, f"Video generation failed: {result.stderr}")
        
        # Verify output
        if not os.path.exists(output_path):
            logger.error("Output file not created")
            raise HTTPException(500, "Output file not generated")
        
        file_size = os.path.getsize(output_path) / (1024 * 1024)  # MB
        
        return JSONResponse(
            content={
                "status": "success",
                "filename": filename,
                "download_url": f"/download/{filename}",
                "details": {
                    "text": req.text,
                    "duration": req.duration,
                    "resolution": f"{req.width}x{req.height}",
                    "size_mb": round(file_size, 2),
                    "generation_time_sec": round(time.time() - start_time, 2)
                }
            },
            status_code=200
        )
        
    except Exception as e:
        logger.error(f"Generation error: {str(e)}")
        raise HTTPException(500, detail=str(e))

@app.get("/download/{filename}")
async def download_video(filename: str):
    """Download generated video"""
    file_path = f"{OUTPUT_DIR}/{filename}"
    if not os.path.exists(file_path):
        raise HTTPException(404, "File not found")
    
    return FileResponse(
        file_path,
        media_type="video/mp4",
        filename=filename,
        headers={
            "Content-Disposition": f"attachment; filename={filename}",
            "Cache-Control": "no-store"
        }
    )
