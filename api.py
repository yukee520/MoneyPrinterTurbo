from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import FileResponse
import subprocess
import os
import time

app = FastAPI()
os.makedirs("/tmp/outputs", exist_ok=True)

@app.post("/generate")
async def generate_video(request: Request):
    try:
        data = await request.json()
        text = data.get("text", "To the moon!")
        filename = f"video_{int(time.time())}.mp4"
        output_path = f"/tmp/outputs/{filename}"
        
        # Using FFmpeg directly as fallback
        cmd = [
            "ffmpeg",
            "-f", "lavfi",
            "-i", f"color=c=black:s=1200x630:d=5",
            "-vf", f"drawtext=text='{text}':fontsize=50:fontcolor=white:x=(w-text_w)/2:y=(h-text_h)/2",
            "-c:a", "copy",
            output_path
        ]
        
        subprocess.run(cmd, check=True)
        return {"download_url": f"/download/{filename}"}
        
    except Exception as e:
        raise HTTPException(500, detail=str(e))

@app.get("/download/{filename}")
async def download_file(filename: str):
    file_path = f"/tmp/outputs/{filename}"
    if os.path.exists(file_path):
        return FileResponse(file_path)
    raise HTTPException(404, "File not found")
