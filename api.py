@app.post("/generate")
async def generate(request: GenerationRequest):
    try:
        output_file = f"output_{int(time.time())}.mp4"
        output_path = f"/tmp/{output_file}"  # Use /tmp which has write permissions
        
        cmd = [
            "python3",  # Explicitly use python3
            "-m",
            "money_printer_turbo",
            "--text", request.text,
            "--width", str(request.width),
            "--height", str(request.height),
            "--output", output_path
        ]
        
        # Capture output for debugging
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
                    "stderr": result.stderr,
                    "returncode": result.returncode
                }
            )
            
        return {
            "status": "success",
            "download_url": f"/download/{output_file}"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
