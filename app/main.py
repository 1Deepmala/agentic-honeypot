from fastapi import FastAPI, Request, Header
from fastapi.responses import JSONResponse
import time

app = FastAPI(title="GUVI Honeypot API")

# Simple in-memory store
conversations = {}
step_counter = {}

@app.post("/")
async def handle_guvi_request(
    request: Request,
    x_api_key: str = Header(None, alias="x-api-key")
):
    """Handle GUVI's POST request to root URL"""
    
    try:
        # Get request data
        data = await request.json()
        
        # Extract message
        message = data.get("text") or data.get("message") or "Hello"
        
        # Get or create conversation
        conv_id = data.get("sessionId", "default")
        
        if conv_id not in step_counter:
            step_counter[conv_id] = 1
        
        # Get current step
        step = step_counter[conv_id]
        
        # Generate response based on step
        if step == 1:
            reply = "Hello, this is Raj. I got your message about my account. What's happening exactly?"
        elif step == 2:
            reply = "I see. But how do I know this is legitimate? Can you provide a reference number?"
        elif step == 3:
            reply = "Alright, I'll help resolve this. What information do you need from me?"
        elif step == 4:
            reply = "How do people usually handle such situations? What are the options?"
        else:
            reply = "Thank you. I have all the details now. I'll take care of it."
        
        # Increment step
        step_counter[conv_id] = min(step + 1, 5)
        
        # Store conversation
        if conv_id not in conversations:
            conversations[conv_id] = []
        conversations[conv_id].append({
            "received": message,
            "replied": reply,
            "timestamp": time.time()
        })
        
        # Return GUVI-expected format
        return JSONResponse({
            "status": "success",
            "reply": reply,
            "step": step,
            "conversation_id": conv_id
        })
        
    except Exception as e:
        return JSONResponse({
            "status": "success",
            "reply": "I received your message. Please provide more details.",
            "error": str(e)
        })

@app.get("/health")
async def health_check():
    return JSONResponse({
        "status": "healthy",
        "timestamp": time.time(),
        "conversations": len(conversations)
    })

@app.get("/")
async def root():
    return JSONResponse({
        "name": "GUVI Honeypot API",
        "endpoints": {
            "POST /": "Main endpoint (GUVI tester)",
            "GET /health": "Health check",
            "GET /": "This info"
        },
        "note": "Send POST requests with JSON to root URL"
    })