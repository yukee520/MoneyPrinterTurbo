from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
import subprocess
import os
from typing import Optional
from pydantic import BaseModel

app = FastAPI()

# Create output directory if it doesn't exist
os.makedirs("outputs", exist_ok=True)

class GenerationRequest(BaseModel):
    text: str = "To the moon!"
    width: int = 1200
    height: int = 630
    background_color: str = "#000000"
    text_color: str = "#FFFFFF"
    output_filename: Optional[str] = None

@app.get("/")
def root():
    return {"message": "Money Printer Turbo API is live", "docs": "/docs"}

@app.post("/generate")
async def generate(request: GenerationRequest):
    try:
        # Generate unique filename if none provided
        output_file = request.output_filename or f"output_{int(time.time())}.mp4"
        output_path = f"outputs/{output_file}"
        
        # Build the command to run Money Printer Turbo
        cmd = [
            "python", 
            "-m", 
            "money_printer_turbo",
            "--text", request.text,
            "--width", str(request.width),
            "--height", str(request.height),
            "--background_color", request.background_color,
            "--text_color", request.text_color,
            "--output", output_path
        ]
        
        # Execute the command
        subprocess.run(cmd, check=True)
        
        # Verify file was created
        if not os.path.exists(output_path):
            raise HTTPException(status_code=500, detail="Video generation failed")
            
        return {
            "status": "success",
            "message": "Video generated successfully",
            "download_url": f"/download/{output_file}"
        }
        
    except subprocess.CalledProcessError as e:
        raise HTTPException(status_code=500, detail=f"Generation failed: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/download/{filename}")
async def download_file(filename: str):
    file_path = f"outputs/{filename}"
    if os.path.exists(file_path):
        return FileResponse(file_path, media_type='video/mp4', filename=filename)
    raise HTTPException(status_code=404, detail="File not found")

# Only expose the outputs directory, not the entire filesystem
app.mount("/outputs", StaticFiles(directory="outputs"), name="outputs")
