from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import FileResponse
import subprocess
import os
import time
import sys

# Initialize FastAPI app
app = FastAPI()

# Ensure outputs directory exists
os.makedirs("/tmp/outputs", exist_ok=True)

@app.get("/")
async def root():
    return {
        "message": "Money Printer Turbo API is live",
        "endpoints": {
            "docs": "/docs",
            "generate": "POST /generate",
            "download": "GET /download/{filename}"
        }
    }

@app.post("/generate")
async def generate_video(request: Request):
    """Generate a money printer video with custom text"""
    try:
        # Get request data
        data = await request.json()
        text = data.get("text", "To the moon!")
        
        # Create unique filename
        timestamp = int(time.time())
        filename = f"video_{timestamp}.mp4"
        output_path = f"/tmp/outputs/{filename}"
        
        # Verify money_printer_turbo is installed
        try:
            import money_printer_turbo
        except ImportError:
            # Attempt to install if missing
            subprocess.run([
                sys.executable, "-m", "pip", "install",
                "git+https://github.com/yukee520/money-printer-turbo.git"
            ], check=True)
            import money_printer_turbo
        
        # Generate video (using direct function call)
        from money_printer_turbo import generate_video as generate
        generate(
            text=text,
            output=output_path,
            width=1200,
            height=630
        )
        
        return {
            "status": "success",
            "filename": filename,
            "download_url": f"/download/{filename}",
            "timestamp": timestamp
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={
                "error": str(e),
                "solution": "Check server logs for installation issues"
            }
        )

@app.get("/download/{filename}")
async def download_video(filename: str):
    """Download generated video file"""
    file_path = f"/tmp/outputs/{filename}"
    if os.path.exists(file_path):
        return FileResponse(
            file_path,
            media_type="video/mp4",
            filename=filename
        )
    raise HTTPException(
        status_code=404,
        detail="File not found. It may have expired or was never generated."
    )
