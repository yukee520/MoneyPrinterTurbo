from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import FileResponse
import subprocess
import os
import time

# Initialize FastAPI app
app = FastAPI()

# Create output directory if it doesn't exist
os.makedirs("/tmp/outputs", exist_ok=True)

@app.get("/")
async def root():
    return {"message": "Money Printer Turbo API is live", "docs": "/docs"}

@app.post("/generate")
async def generate(request: Request):
    try:
        # Get JSON data from request
        data = await request.json()
        text = data.get("text", "Default text")
        
        # Generate filename
        filename = f"video_{int(time.time())}.mp4"
        output_path = f"/tmp/outputs/{filename}"
        
        # Run money printer turbo (simplified command)
        cmd = [
            "python3",
            "-m",
            "money_printer_turbo",
            "--text", text,
            "--output", output_path
        ]
        
        # Run command with error capturing
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True
        )
        
        if result.returncode != 0:
            raise HTTPException(
                status_code=500,
                detail={
                    "error": "Generation failed",
                    "stdout": result.stdout,
                    "stderr": result.stderr
                }
            )
            
        return {
            "status": "success",
            "download_url": f"/download/{filename}"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/download/{filename}")
async def download_file(filename: str):
    file_path = f"/tmp/outputs/{filename}"
    if os.path.exists(file_path):
        return FileResponse(file_path, media_type='video/mp4', filename=filename)
    raise HTTPException(status_code=404, detail="File not found")
