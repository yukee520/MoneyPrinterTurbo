from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse, HTMLResponse
import requests
import os
import logging
from pydantic import BaseModel

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

# HuggingFace Configuration
HF_API_URL = "https://api-inference.huggingface.co/models/deepseek-ai/deepseek-llm-7b"
HF_TOKEN = os.getenv("HF_API_TOKEN")  # Set in Render.com dashboard

# Root endpoint - Essential for Render.com health checks
@app.get("/", response_class=HTMLResponse)
async def root():
    return """
    <html>
        <body>
            <h1>Money Printer Turbo API</h1>
            <p>Endpoints:</p>
            <ul>
                <li><b>POST /generate-script</b> - Generate viral scripts</li>
                <li><b>GET /health</b> - Service status</li>
            </ul>
        </body>
    </html>
    """

# Health check endpoint
@app.get("/health")
async def health_check():
    return {"status": "healthy", "model": "deepseek-llm-7b"}

class ScriptRequest(BaseModel):
    title: str
    style: str = "viral"
    max_length: int = 150

@app.post("/generate-script")
async def generate_script(request: ScriptRequest):
    try:
        # Prepare prompt for DeepSeek
        prompt = f"""
        Create a 15-second {request.style} video script about: {request.title}
        Required format:
        [HOOK] <3-second attention grabber>
        [CONTENT] <valuable information>
        [CTA] <strong call-to-action>
        """
        
        # Call HuggingFace API
        headers = {"Authorization": f"Bearer {HF_TOKEN}"}
        response = requests.post(
            HF_API_URL,
            headers=headers,
            json={"inputs": prompt, "parameters": {"max_new_tokens": request.max_length}},
            timeout=20
        )
        
        if response.status_code != 200:
            logger.error(f"HuggingFace error: {response.text}")
            return generate_fallback_script(request.title, request.style)
            
        script = response.json()[0]["generated_text"]
        
        # Ensure required sections exist
        if not all(tag in script for tag in ["[HOOK]", "[CONTENT]", "[CTA]"]):
            script = format_script(script, request.title)
            
        return JSONResponse({
            "status": "success",
            "script": script,
            "model": "deepseek-llm-7b"
        })
        
    except Exception as e:
        logger.error(f"Error: {str(e)}")
        return generate_fallback_script(request.title, request.style)

def format_script(raw_text: str, title: str) -> str:
    """Ensure script has proper structure"""
    return f"""
    [HOOK] Did you know about {title}?
    [CONTENT] {raw_text[:100]}...
    [CTA] Follow for more!
    """

def generate_fallback_script(title: str, style: str) -> JSONResponse:
    """Local template fallback"""
    templates = {
        "viral": f"[HOOK] This {title} hack went viral!\n[CONTENT] Experts hate this...\n[CTA] Like & share!",
        "educational": f"[HOOK] The truth about {title}\n[CONTENT] Research shows...\n[CTA] Follow for tips!"
    }
    return JSONResponse({
        "status": "fallback",
        "script": templates.get(style, templates["viral"]),
        "model": "template"
    })
