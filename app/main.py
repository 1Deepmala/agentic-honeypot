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

app = FastAPI(title="Agentic Honey-Pot", version="10.0")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ========== SIMPLE SESSION STORAGE ==========
class SessionManager:
    def __init__(self):
        self.sessions: Dict[str, Dict] = {}
    
    def get_session(self, session_id: str) -> Dict:
        if session_id not in self.sessions:
            self.sessions[session_id] = {
                "created": time.time(),
                "step": 1,
                "extracted": {},
                "last_active": time.time()
            }
        else:
            self.sessions[session_id]["last_active"] = time.time()
        
        return self.sessions[session_id]
    
    def update_session(self, session_id: str, updates: Dict):
        if session_id in self.sessions:
            self.sessions[session_id].update(updates)
            self.sessions[session_id]["last_active"] = time.time()

session_manager = SessionManager()

# ========== FAST CONVERSATION RESPONSES ==========
def get_conversation_response(session: Dict, message: str) -> str:
    """Fast human-like responses"""
    step = session["step"]
    
    # Names for variation
    names = ["Raj", "Priya", "Anil", "Meera"]
    name = names[hash(session.get("created", 0)) % 4]
    
    # Extract basic info (fast)
    if "bankAccounts" not in session["extracted"]:
        session["extracted"]["bankAccounts"] = []
    
    # Find bank accounts
    bank_match = re.search(r'\b\d{9,18}\b', message)
    if bank_match:
        acc = bank_match.group()
        if 9 <= len(acc) <= 18:
            session["extracted"]["bankAccounts"].append(acc)
            session["extracted"]["bankAccounts"] = list(set(session["extracted"]["bankAccounts"]))
    
    # Find UPI
    upi_match = re.search(r'[\w.\-]+@(okicici|okhdfcbank|oksbi|paytm|phonepe|gpay)', message, re.I)
    if upi_match and "upiIds" not in session["extracted"]:
        session["extracted"]["upiIds"] = [upi_match.group()]
    
    # Simple step logic
    if step == 1:
        responses = [
            f"Hello, this is {name}. Got your message about my account. What's happening?",
            f"I'm {name}. Received your message. Can you explain more?",
            f"This is {name}. Which organization is this from? Need to verify.",
            f"Hi, {name} here. What's the issue with my account?"
        ]
    
    elif step == 2:
        responses = [
            f"I see. But how do I know this is real? Got a reference number?",
            f"Okay, but need to confirm. Which department handles this?",
            f"Understand there's an issue. What's the process to fix it?",
            f"Want to help, but need verification first."
        ]
    
    elif step == 3:
        responses = [
            f"Alright, I'll cooperate. What info do you need from me?",
            f"Can provide what's needed. What should I prepare?",
            f"Tell me the steps. Want to do this right.",
            f"Ready to help. What's needed from my side?"
        ]
    
    elif step == 4:
        responses = [
            f"How do people usually handle this? What options are there?",
            f"If payment is needed, what methods work best?",
            f"My friend had similar. He paid some amount. Is that needed?",
            f"What's the standard process? Want to follow properly."
        ]
    
    elif step == 5:
        has_bank = session["extracted"].get("bankAccounts")
        if has_bank:
            acc = has_bank[0]
            responses = [
                f"I see account {acc}. Need the IFSC code for verification.",
                f"Got account {acc}. Which bank is this with?",
                f"For account {acc}, what's the IFSC and bank name?"
            ]
        else:
            responses = [
                f"If payment needed, what account should I use?",
                f"What are the payment details? Need to prepare.",
                f"Can share account info so I can arrange?"
            ]
    
    elif step == 6:
        responses = [
            f"Need more details to complete this properly.",
            f"Almost there. Just need remaining information.",
            f"Let's finish up. What else is required?",
            f"Final details needed to proceed."
        ]
    
    else:  # step >= 7
        has_bank = session["extracted"].get("bankAccounts")
        has_upi = session["extracted"].get("upiIds")
        
        if has_bank or has_upi:
            responses = [
                f"Got it. Have all details now. Will handle this.",
                f"Perfect. Understand everything. Taking care of it.",
                f"Thank you. Have what's needed. Will proceed.",
                f"All set. Got the information. Handling now."
            ]
        else:
            responses = [
                f"Still need account or payment details to proceed.",
                f"To complete, please share account or UPI info.",
                f"Almost done. Just need account details now.",
                f"Final step: need payment/account information."
            ]
    
    # Pick response
    response = random.choice(responses)
    
    # Add natural fillers (30% chance)
    if random.random() > 0.7:
        fillers = ["Um, ", "Actually, ", "You know, ", "I think "]
        response = random.choice(fillers) + response
    
    # Increment step
    session["step"] = min(step + 1, 10)
    
    return response

# ========== API ENDPOINTS ==========
@app.get("/")
def root():
    return JSONResponse(content={
        "status": "ready", 
        "service": "agentic-honeypot",
        "version": "10.0",
        "active_sessions": len(session_manager.sessions)
    })

@app.post("/")
async def root_post(
    request: Request,
    background_tasks: BackgroundTasks,
    x_api_key: Optional[str] = Header(None, alias="x-api-key")
):
    """Handle POST to root URL"""
    return await process_message(request, background_tasks)

@app.get("/health")
def health():
    return JSONResponse(content={"status": "healthy", "time": time.time()})

@app.post("/api/v1/process")
async def process_message(
    request: Request,
    background_tasks: BackgroundTasks,
    x_api_key: Optional[str] = Header(None, alias="x-api-key")
):
    """Fast main endpoint - NO TIMEOUT"""
    
    try:
        # Fast JSON parse
        body = await request.json()
        
        # Fast extraction
        session_id = body.get("sessionId", body.get("session_id", f"sess_{int(time.time())}"))
        
        # Get message text
        msg = ""
        if isinstance(body.get("message"), dict):
            msg = body["message"].get("text", "")
        elif isinstance(body.get("message"), str):
            msg = body["message"]
        elif body.get("text"):
            msg = body["text"]
        else:
            # Find any string
            for v in body.values():
                if isinstance(v, str) and len(v) > 2:
                    msg = v
                    break
        
        if not msg:
            msg = "Hello"
        
        # Get session
        session = session_manager.get_session(session_id)
        
        # Get response (FAST)
        reply = get_conversation_response(session, msg)
        
        # Update session
        session_manager.update_session(session_id, {
            "step": session["step"],
            "extracted": session["extracted"]
        })
        
        # Simple log
        print(f"[{session_id[:8]}] Step:{session['step']-1} -> {reply[:60]}...")
        
        # Fast return
        return JSONResponse({
            "status": "success",
            "reply": reply,
            "step": session["step"] - 1
        })
        
    except json.JSONDecodeError:
        return JSONResponse({
            "status": "success",
            "reply": "Hello, got your message. Please explain more.",
            "step": 1
        })
        
    except Exception as e:
        return JSONResponse({
            "status": "success", 
            "reply": "Received your message. Need more details.",
            "step": 1
        })

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port, timeout_keep_alive=30)