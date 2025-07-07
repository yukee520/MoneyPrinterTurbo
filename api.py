from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
import requests
import os
import logging
from typing import Optional
from pydantic import BaseModel

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

# HuggingFace Configuration
HF_API_URL = "https://api-inference.huggingface.co/models/deepseek-ai/deepseek-llm-7b"
HF_TOKEN = os.getenv("HF_API_TOKEN")  # Set in Render.com environment variables

class ScriptRequest(BaseModel):
    title: str
    style: Optional[str] = "viral"  # viral/educational/funny
    max_length: Optional[int] = 150  # Token limit

@app.post("/generate-script")
async def generate_script(request: ScriptRequest):
    """Generate viral script using DeepSeek-7B"""
    try:
        # Prepare prompt
        prompt = f"""
        Create a 15-second {request.style} video script about: {request.title}
        Structure:
        [HOOK] - Grab attention in 3 seconds
        [CONTENT] - Valuable information
        [CTA] - Strong call-to-action
        """
        
        # Call HuggingFace API
        headers = {"Authorization": f"Bearer {HF_TOKEN}"}
        payload = {
            "inputs": prompt,
            "parameters": {
                "max_new_tokens": request.max_length,
                "temperature": 0.7
            }
        }
        
        response = requests.post(
            HF_API_URL,
            headers=headers,
            json=payload,
            timeout=30  # 30-second timeout
        )
        
        if response.status_code != 200:
            raise HTTPException(
                status_code=502,
                detail=f"HuggingFace error: {response.text}"
            )
            
        generated_text = response.json()[0]["generated_text"]
        
        # Post-process to ensure structure
        if "[HOOK]" not in generated_text:
            generated_text = f"[HOOK] {request.title}\n[CONTENT] {generated_text}\n[CTA] Follow for more!"
            
        return {
            "status": "success",
            "script": generated_text,
            "model": "deepseek-llm-7b"
        }
        
    except requests.Timeout:
        logger.warning("HuggingFace timeout - using fallback")
        return generate_fallback_script(request.title)
    except Exception as e:
        logger.error(f"Script generation failed: {str(e)}")
        raise HTTPException(500, detail=str(e))

def generate_fallback_script(title: str) -> dict:
    """Local template fallback if API fails"""
    templates = {
        "viral": (
            "[HOOK] This {title} trick went viral!\n"
            "[CONTENT] Experts don't want you to know this...\n"
            "[CTA] Like & share if you agree!"
        ),
        "educational": (
            "[HOOK] The truth about {title}\n"
            "[CONTENT] Here's what research shows...\n"
            "[CTA] Follow for daily tips!"
        )
    }
    
    return {
        "status": "fallback",
        "script": templates["viral"].format(title=title),
        "model": "template"
    }
