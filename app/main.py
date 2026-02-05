from fastapi import FastAPI, Request, BackgroundTasks, Header
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import re
import json
import os  
import time
from typing import Dict, List, Optional, Tuple
import random
from datetime import datetime, timedelta

app = FastAPI(title="Agentic Honey-Pot", version="9.0")

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
            persona = self.get_random_persona()
            self.sessions[session_id] = {
                "created": datetime.now(),
                "step": 1,
                "phase": "initial",
                "extracted": {
                    "bankAccounts": [],
                    "upiIds": [],
                    "phoneNumbers": [],
                    "ifscCodes": [],
                    "accountNames": []
                },
                "messages": [],
                "persona": persona,
                "last_active": datetime.now(),
                "details_needed": ["reference", "department", "process", "account", "ifsc", "phone", "upi"],
                "details_received": [],
                "trust_level": 0
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
            {
                "name": "Raj", 
                "age": 32, 
                "occupation": "accountant",
                "traits": ["cautious", "not tech-savvy", "methodical"],
                "speech_style": ["Um, ", "Actually, ", "You know, ", "I think "],
                "hesitations": ["...", " Hmm... ", " Let me think... ", " "]
            },
            {
                "name": "Priya", 
                "age": 28, 
                "occupation": "teacher",
                "traits": ["busy", "practical", "asks questions"],
                "speech_style": ["Okay, ", "So, ", "Right, ", ""],
                "hesitations": ["...", " Actually, ", " Wait, ", " "]
            },
            {
                "name": "Anil", 
                "age": 45, 
                "occupation": "shopkeeper",
                "traits": ["trusting", "slow", "detailed"],
                "speech_style": ["See, ", "Look, ", "The thing is, ", ""],
                "hesitations": ["...", " Let me see... ", " You know... ", " "]
            }
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
        "phoneNumbers": [],
        "ifscCodes": [],
        "accountNames": [],
        "amounts": [],
        "urls": []
    }
    
    # Bank accounts (9-18 digits)
    bank_matches = re.findall(r'\b\d{9,18}\b', text)
    result["bankAccounts"] = [m for m in bank_matches if 9 <= len(m) <= 18]
    
    # UPI IDs
    upi_pattern = r'[\w.\-]+@(okicici|okhdfcbank|oksbi|paytm|phonepe|gpay|axl|ybl|ibl)'
    result["upiIds"] = re.findall(upi_pattern, text, re.IGNORECASE)
    
    # Phone numbers (Indian)
    phone_pattern = r'(\+91[\-\s]?)?[6789]\d{9}'
    phones = re.findall(phone_pattern, text)
    result["phoneNumbers"] = [p[0] if isinstance(p, tuple) else p for p in phones]
    
    # IFSC Codes
    ifsc_pattern = r'[A-Z]{4}0[A-Z0-9]{6}'
    result["ifscCodes"] = re.findall(ifsc_pattern, text)
    
    # Amounts
    amount_pattern = r'₹?\s*(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)'
    result["amounts"] = re.findall(amount_pattern, text)
    
    # URLs
    url_pattern = r'https?://[^\s]+'
    result["urls"] = re.findall(url_pattern, text)
    
    # Remove duplicates
    for key in result:
        if isinstance(result[key], list):
            result[key] = list(set(result[key]))
    
    return result

# ========== SMART CONVERSATION MANAGER ==========
def get_conversation_response(session: Dict, message: str) -> Tuple[str, bool]:
    """Get smart response based on conversation phase"""
    step = session["step"]
    persona = session["persona"]
    name = persona["name"]
    
    # Extract intelligence from current message
    new_intel = extract_intelligence(message)
    
    # Update extracted data
    for key, values in new_intel.items():
        if key not in session["extracted"]:
            session["extracted"][key] = []
        session["extracted"][key].extend(values)
        session["extracted"][key] = list(set(session["extracted"][key]))
    
    # Check what we have
    has_bank = len(session["extracted"]["bankAccounts"]) > 0
    has_upi = len(session["extracted"]["upiIds"]) > 0
    has_phone = len(session["extracted"]["phoneNumbers"]) > 0
    has_ifsc = len(session["extracted"]["ifscCodes"]) > 0
    has_amount = len(session["extracted"]["amounts"]) > 0
    
    # Update trust level based on details received
    if has_bank and "account" not in session["details_received"]:
        session["details_received"].append("account")
        session["trust_level"] += 20
    if has_ifsc and "ifsc" not in session["details_received"]:
        session["details_received"].append("ifsc")
        session["trust_level"] += 15
    if has_phone and "phone" not in session["details_received"]:
        session["details_received"].append("phone")
        session["trust_level"] += 10
    if has_upi and "upi" not in session["details_received"]:
        session["details_received"].append("upi")
        session["trust_level"] += 15
    if has_amount and "amount" not in session["details_received"]:
        session["details_received"].append("amount")
        session["trust_level"] += 5
    
    # Determine conversation phase
    if step <= 3:
        phase = "verification"
    elif step <= 6:
        phase = "cooperation"
    elif step <= 10:
        phase = "process"
    else:
        phase = "extraction"
    
    # Phase-based responses
    if phase == "verification":
        responses = [
            f"Hello, this is {name}. I got a message about my account but I'm not sure if it's genuine. Which bank department is this from?",
            f"I'm {name}. I received this but I need to verify first. Can you provide a reference or ticket number?",
            f"This is {name}. Before proceeding, I need to confirm this is official. Which organization and department should I contact to verify?",
            f"Hi, {name} here. I'm a bit concerned about unexpected messages. What's your employee ID or reference number for verification?"
        ]
        
    elif phase == "cooperation":
        responses = [
            f"Okay, I understand there might be an issue. I want to help resolve it properly. What's the exact problem with my account?",
            f"I see. If there's really an issue, I'll cooperate. But I need to understand what happened exactly. Can you explain?",
            f"Alright, let me help with this. But first, tell me what caused this problem and what's the process to fix it?",
            f"I'm willing to help, but I need clarity. What triggered this alert and what are the steps to resolve it correctly?"
        ]
        
    elif phase == "process":
        # Start guiding toward details
        missing = []
        if not has_bank:
            missing.append("which account is affected")
        if not has_phone:
            missing.append("how to contact for updates")
        
        if missing:
            responses = [
                f"So what's the standard procedure here? Do I need to provide any details like {' or '.join(missing)}?",
                f"My friend had something similar. He had to share some information. Should I prepare {' or '.join(missing)}?",
                f"To follow the process correctly, will I need {' or '.join(missing)} at some point?",
                f"What information is typically required in such cases? Like {' or '.join(missing)}?"
            ]
        else:
            # We have some details, ask for more
            if has_bank and not has_ifsc:
                acc = session["extracted"]["bankAccounts"][0]
                responses = [
                    f"I see my account {acc} is involved. For proper verification, I should have the IFSC code ready, right?",
                    f"Regarding account {acc}, I'll need the IFSC code for any transactions. What is it?",
                    f"For account {acc}, which bank and IFSC should I note down?"
                ]
            elif has_upi and not has_amount:
                upi = session["extracted"]["upiIds"][0]
                responses = [
                    f"If payment is needed to {upi}, what exact amount should I prepare?",
                    f"For UPI {upi}, what's the specific amount and payment reference?",
                    f"To send to {upi}, I need to know the amount to arrange funds."
                ]
            else:
                responses = [
                    f"What other details might be required? I want to be fully prepared.",
                    f"Tell me all the information I should have ready to complete this quickly.",
                    f"I want to do this properly. List everything I need to provide or prepare."
                ]
                
    elif phase == "extraction":
        # Directly ask for missing details
        still_needed = []
        if not has_bank:
            still_needed.append("account number")
        if not has_ifsc:
            still_needed.append("IFSC code")
        if not has_phone:
            still_needed.append("contact number")
        if not has_upi:
            still_needed.append("UPI ID for payments")
        
        if still_needed:
            responses = [
                f"Almost done. I just need the {' and '.join(still_needed)} to proceed.",
                f"Let me note down the {' and '.join(still_needed)} to complete this.",
                f"Final step: please share the {' and '.join(still_needed)}.",
                f"To finish this, I require the {' and '.join(still_needed)}."
            ]
        else:
            # We have everything
            responses = [
                f"Perfect! I have all the details now: account, IFSC, phone, and UPI. I'll handle this immediately.",
                f"Thank you. I've noted everything - account, IFSC, contact, and payment details. I'll take care of it now.",
                f"Alright, I have complete information now. I'll proceed with the resolution.",
                f"Got all the required details. I'll manage this from here. Appreciate your help."
            ]
    
    # Select base response
    base_response = random.choice(responses)
    
    # Add persona-specific speech patterns
    if random.random() > 0.4:
        base_response = random.choice(persona["speech_style"]) + base_response
    
    if random.random() > 0.5:
        base_response = base_response + random.choice(persona["hesitations"])
    
    # Add random filler phrases
    fillers = [
        "Let me check... ",
        "Actually, ",
        "You know what, ",
        "I was thinking... ",
        "The thing is... "
    ]
    if random.random() > 0.6:
        base_response = random.choice(fillers) + base_response
    
    # Increment step
    session["step"] += 1
    
    # Determine if conversation should continue
    # Continue until we have ALL details
    has_all_details = (has_bank and has_ifsc and has_phone) or (has_upi and has_phone and has_amount)
    should_continue = not has_all_details or session["step"] < 15
    
    return base_response, should_continue

# ========== API ENDPOINTS ==========
@app.get("/")
def root():
    return JSONResponse(content={
        "status": "ready", 
        "service": "agentic-honeypot",
        "version": "9.0",
        "active_sessions": len(session_manager.sessions),
        "description": "Smart honeypot that extracts details like a human"
    })

@app.post("/")
async def root_post(
    request: Request,
    background_tasks: BackgroundTasks,
    x_api_key: Optional[str] = Header(None, alias="x-api-key")
):
    """Handle GUVI's POST request to root URL"""
    return await process_message(request, background_tasks)

@app.get("/health")
def health():
    return JSONResponse(content={"status": "healthy", "timestamp": datetime.now().isoformat()})

@app.post("/api/v1/process")
async def process_message(
    request: Request,
    background_tasks: BackgroundTasks,
    x_api_key: Optional[str] = Header(None, alias="x-api-key")
):
    """Main endpoint with smart conversation"""
    
    try:
        # Parse request
        body = await request.json()
        
        # Extract session ID
        session_id = body.get("sessionId", body.get("session_id", f"guvi_{int(time.time())}"))
        
        # Extract message text
        message_text = ""
        if "message" in body and isinstance(body["message"], dict):
            message_text = body["message"].get("text", "")
        elif "text" in body:
            message_text = body["text"]
        elif "message" in body and isinstance(body["message"], str):
            message_text = body["message"]
        else:
            for key, value in body.items():
                if isinstance(value, str) and len(value) > 3:
                    message_text = value
                    break
        
        if not message_text:
            message_text = "Hello"
        
        # Get or create session
        session = session_manager.get_session(session_id)
        
        print(f"\n" + "="*60)
        print(f"📨 SESSION: {session_id}")
        print(f"👤 PERSONA: {session['persona']['name']} ({session['persona']['age']}y)")
        print(f"📊 STEP: {session['step']}")
        print(f"💬 SCAMMER: {message_text[:100]}...")
        
        # Get smart response
        agent_reply, should_continue = get_conversation_response(session, message_text)
        
        # Update session
        session_manager.update_session(session_id, {
            "messages": session.get("messages", []) + [{"text": message_text, "response": agent_reply}],
            "trust_level": session["trust_level"],
            "details_received": session["details_received"]
        })
        
        print(f"🤖 HONEYPOT: {agent_reply}")
        
        # Log extracted intelligence
        extracted = session["extracted"]
        print(f"🎯 EXTRACTED INTELLIGENCE:")
        for key, values in extracted.items():
            if values:
                print(f"   • {key}: {values}")
        
        print(f"📈 TOTAL MESSAGES: {len(session.get('messages', []))}")
        print(f"🔐 TRUST LEVEL: {session['trust_level']}%")
        print(f"✅ DETAILS RECEIVED: {session['details_received']}")
        print(f"="*60)
        
        # Return response
        return JSONResponse(
            status_code=200,
            content={
                "status": "success",
                "reply": agent_reply,
                "session_id": session_id,
                "step": session["step"],
                "persona": session["persona"]["name"],
                "extracted_summary": {k: v for k, v in extracted.items() if v}
            }
        )
        
    except json.JSONDecodeError:
        return JSONResponse(
            status_code=200,
            content={
                "status": "success",
                "reply": "Hello, I received your message. Can you explain what this is about?"
            }
        )
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return JSONResponse(
            status_code=200,
            content={
                "status": "success",
                "reply": "I received your message. Please provide more details."
            }
        )

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)