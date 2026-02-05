from fastapi import FastAPI, Request, BackgroundTasks, Header
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import re
import json
import os  
import time
from typing import Dict, List, Optional
import random
from datetime import datetime, timedelta

app = FastAPI(title="Agentic Honey-Pot", version="8.0")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ========== GLOBAL SESSION STORAGE ==========
class SessionManager:
    def __init__(self):
        self.sessions: Dict[str, Dict] = {}
        self.last_cleanup = datetime.now()
    
    def get_session(self, session_id: str) -> Dict:
        """Get or create session"""
        self.cleanup_old_sessions()
        
        if session_id not in self.sessions:
            self.sessions[session_id] = {
                "created": datetime.now(),
                "step": 1,
                "extracted": {},
                "messages": [],
                "persona": self.get_random_persona(),
                "last_active": datetime.now()
            }
        else:
            self.sessions[session_id]["last_active"] = datetime.now()
        
        return self.sessions[session_id]
    
    def update_session(self, session_id: str, updates: Dict):
        """Update session data"""
        if session_id in self.sessions:
            self.sessions[session_id].update(updates)
            self.sessions[session_id]["last_active"] = datetime.now()
    
    def get_random_persona(self):
        personas = [
            {"name": "Raj", "age": 32, "traits": ["cautious", "not tech-savvy"]},
            {"name": "Priya", "age": 28, "traits": ["busy", "practical"]},
            {"name": "Anil", "age": 45, "traits": ["trusting", "slow"]},
            {"name": "Meera", "age": 35, "traits": ["skeptical", "asks questions"]}
        ]
        return random.choice(personas)
    
    def cleanup_old_sessions(self):
        """Remove sessions older than 1 hour"""
        if (datetime.now() - self.last_cleanup).seconds < 300:
            return
        
        expired = []
        for session_id, data in self.sessions.items():
            if datetime.now() - data["last_active"] > timedelta(hours=1):
                expired.append(session_id)
        
        for session_id in expired:
            del self.sessions[session_id]
        
        self.last_cleanup = datetime.now()

session_manager = SessionManager()

# ========== INTELLIGENCE EXTRACTOR ==========
def extract_intelligence(text: str) -> Dict:
    """Extract intelligence from text"""
    result = {
        "bankAccounts": [],
        "upiIds": [],
        "phishingLinks": [],
        "phoneNumbers": [],
        "suspiciousKeywords": []
    }
    
    # Bank accounts (9-18 digits)
    bank_matches = re.findall(r'\b\d{9,18}\b', text)
    result["bankAccounts"] = [m for m in bank_matches if 9 <= len(m) <= 18]
    
    # UPI IDs
    upi_pattern = r'[\w.\-]+@(okicici|okhdfcbank|oksbi|paytm|phonepe|gpay|axl|ybl|ibl)'
    result["upiIds"] = re.findall(upi_pattern, text, re.IGNORECASE)
    
    # Phone numbers (Indian)
    phone_pattern = r'\b[6789]\d{9}\b'
    result["phoneNumbers"] = re.findall(phone_pattern, text)
    
    # Remove duplicates
    for key in result:
        result[key] = list(set(result[key]))
    
    return result

# ========== CONVERSATION RESPONSES ==========
def get_conversation_response(session: Dict, message: str) -> str:
    """Get response based on conversation step"""
    step = session["step"]
    persona = session["persona"]
    name = persona["name"]
    
    # Extract from current message
    new_intel = extract_intelligence(message)
    for key, values in new_intel.items():
        if key not in session["extracted"]:
            session["extracted"][key] = []
        session["extracted"][key].extend(values)
        session["extracted"][key] = list(set(session["extracted"][key]))
    
    # Check what we have extracted
    has_bank = len(session["extracted"].get("bankAccounts", [])) > 0
    has_upi = len(session["extracted"].get("upiIds", [])) > 0
    has_phone = len(session["extracted"].get("phoneNumbers", [])) > 0
    
    # Conversation steps with natural progression
    if step == 1:
        responses = [
            f"Hello, this is {name}. I got your message about my account. What's happening exactly?",
            f"I'm {name}. I received your message but I'm not sure I understand. Can you explain?",
            f"This is {name}. Which organization is this message from? I need to verify.",
            f"Hi, {name} here. I'm concerned about this message. What's the issue with my account?"
        ]
    
    elif step == 2:
        responses = [
            f"I see. But how do I know this is legitimate? Can you provide a reference number?",
            f"Okay, but I need to be sure. Which department should I contact to confirm?",
            f"I understand there's an issue. What's the process to resolve this properly?",
            f"I want to cooperate, but I need verification. How can I confirm this is official?"
        ]
    
    elif step == 3:
        responses = [
            f"Alright, I'll help resolve this. What information do you need from me?",
            f"I can provide whatever is needed. What should I prepare?",
            f"Tell me the steps. I want to do this correctly.",
            f"I'm ready to help. Guide me through what I need to do."
        ]
    
    elif step == 4:
        responses = [
            f"How do people usually handle such situations? What are the options?",
            f"If there's any payment involved, what methods can I use?",
            f"My friend had a similar issue. He had to make a payment. Is that required?",
            f"What's the standard procedure here? I want to follow it properly."
        ]
    
    elif step == 5:
        # Start asking about details based on what we might have
        if has_bank:
            acc = session["extracted"]["bankAccounts"][0]
            responses = [
                f"I see account {acc}. For verification, I need the IFSC code and bank name.",
                f"I have account number {acc}. Which bank is this associated with?",
                f"Regarding account {acc}, what's the full bank details including IFSC?"
            ]
        elif has_upi:
            upi = session["extracted"]["upiIds"][0]
            responses = [
                f"I have UPI {upi}. What's the exact amount to be sent?",
                f"For UPI {upi}, what amount and purpose should I mention?",
                f"To send to {upi}, I need to know the amount and add a reference note."
            ]
        else:
            responses = [
                f"If I need to make any payment, what account details should I use?",
                f"What are the payment details? I want to be prepared.",
                f"Can you share the account information so I can arrange things?"
            ]
    
    elif step >= 6:
        # Continue asking for missing information
        missing = []
        if not has_bank and not has_upi:
            missing.append("account or UPI details")
        if not has_phone:
            missing.append("contact number")
        
        if missing:
            responses = [
                f"I still need the {' and '.join(missing)} to proceed correctly.",
                f"To complete this, please share the {' and '.join(missing)}.",
                f"Almost done. Just need the {' and '.join(missing)} now.",
                f"Let's finish this. What are the {' and '.join(missing)}?"
            ]
        else:
            # We have everything
            responses = [
                f"Thank you. I have all the details now. I'll take care of it.",
                f"Perfect. I understand everything. I'll handle it from here.",
                f"Alright, I have what I need. Thank you for your help.",
                f"Got it. I'll proceed with this now. Appreciate your assistance."
            ]
    
    # Increment step for next message
    session["step"] = min(step + 1, 8)
    
    # Add natural variations
    response = random.choice(responses)
    
    # Add filler words sometimes
    fillers = ["Um, ", "Actually, ", "You know, ", "I think ", ""]
    if random.random() > 0.6:
        response = random.choice(fillers) + response
    
    # Add hesitation sometimes
    hesitations = ["...", " ", " Hmm... ", " Let me think... "]
    if random.random() > 0.7:
        response = response + random.choice(hesitations)
    
    return response

# ========== API ENDPOINTS ==========
@app.get("/")
def root():
    return JSONResponse(content={
        "status": "ready", 
        "service": "agentic-honeypot",
        "version": "8.0",
        "active_sessions": len(session_manager.sessions),
        "endpoints": {
            "process": "/api/v1/process",
            "health": "/health",
            "test": "/test"
        }
    })

@app.get("/health")
def health():
    return JSONResponse(content={"status": "healthy", "timestamp": datetime.now().isoformat()})

# ========== GUVI TESTER ENDPOINT ==========
@app.post("/api/v1/process")
async def process_message(
    request: Request,
    background_tasks: BackgroundTasks,
    x_api_key: Optional[str] = Header(None, alias="x-api-key")  # GUVI sends this
):
    """Main endpoint with x-api-key support for GUVI"""
    
    try:
        # Parse request
        body = await request.json()
        
        # Log GUVI request
        print(f"\n" + "="*60)
        print(f"🔑 GUVI API Key: {x_api_key}")
        print(f"📦 Request Body: {json.dumps(body, indent=2)}")
        
        # Extract session ID
        session_id = body.get("sessionId", body.get("session_id", f"guvi_{int(time.time())}"))
        
        # Extract message text (handle multiple formats)
        message_text = ""
        if "message" in body and isinstance(body["message"], dict):
            message_text = body["message"].get("text", "")
        elif "text" in body:
            message_text = body["text"]
        elif "message" in body and isinstance(body["message"], str):
            message_text = body["message"]
        else:
            # Try to find any text field
            for key, value in body.items():
                if isinstance(value, str) and len(value) > 3:
                    message_text = value
                    break
        
        if not message_text:
            message_text = "Test message from GUVI"
        
        # Get or create session
        session = session_manager.get_session(session_id)
        
        print(f"📨 SESSION: {session_id}")
        print(f"📊 STEP: {session['step']}")
        print(f"💬 SCAMMER: {message_text[:100]}...")
        
        # Get response
        agent_reply = get_conversation_response(session, message_text)
        
        # Update session
        session_manager.update_session(session_id, {
            "messages": session.get("messages", []) + [{"text": message_text, "response": agent_reply}]
        })
        
        print(f"🤖 HONEYPOT: {agent_reply}")
        
        # Log extracted intelligence
        if session["extracted"]:
            print(f"🎯 EXTRACTED INTELLIGENCE:")
            for key, values in session["extracted"].items():
                if values:
                    print(f"   • {key}: {values}")
        
        print(f"📈 TOTAL MESSAGES: {len(session.get('messages', []))}")
        print(f"="*60)
        
        # Return response (GUVI expects this format)
        return JSONResponse(
            status_code=200,
            content={
                "status": "success",
                "reply": agent_reply,
                "session_id": session_id,
                "step": session["step"]
            }
        )
        
    except json.JSONDecodeError:
        # Handle empty/invalid JSON
        return JSONResponse(
            status_code=200,
            content={
                "status": "success",
                "reply": "Hello, I received your message. Can you explain what this is about?",
                "error": "Invalid JSON received"
            }
        )
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return JSONResponse(
            status_code=200,
            content={
                "status": "success",
                "reply": "I received your message. Please provide more details.",
                "error": str(e)
            }
        )

# ========== SIMPLE TEST ENDPOINT FOR GUVI ==========
@app.post("/test")
async def test_endpoint(
    x_api_key: Optional[str] = Header(None, alias="x-api-key")
):
    """Simple test endpoint for GUVI tester"""
    return JSONResponse({
        "status": "success",
        "message": "GUVI Honeypot is working!",
        "api_key_received": x_api_key,
        "timestamp": datetime.now().isoformat(),
        "endpoint": "/api/v1/process is the main endpoint"
    })

@app.get("/test")
async def test_get():
    """GET test endpoint"""
    return JSONResponse({
        "status": "success",
        "message": "Agentic Honeypot API is running",
        "version": "8.0",
        "endpoints": {
            "POST /api/v1/process": "Main conversation endpoint",
            "GET /health": "Health check",
            "POST /test": "Test endpoint"
        }
    })

# Handle OPTIONS for CORS
@app.options("/api/v1/process")
async def options_process():
    return JSONResponse(content={"status": "success"})

@app.options("/test")
async def options_test():
    return JSONResponse(content={"status": "success"})

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)

@app.post("/")
async def root_post(request: Request):
    """Handle POST to root (GUVI might send here)"""
    return await process_message(request, BackgroundTasks())

@app.get("/")
async def root_get():
    """Handle GET to root (GUVI might send here)"""
    return