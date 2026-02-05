from fastapi import FastAPI, Request, Header, BackgroundTasks
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import re
import json
import os  
import time
import random
import requests
from typing import Dict, List

app = FastAPI(title="GUVI Honeypot", version="2.0")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ========== SESSION MANAGEMENT ==========
sessions = {}
GUVI_CALLBACK_URL = "https://hackathon.guvi.in/api/updateHoneyPotFinalResult"

def get_session(session_id: str) -> Dict:
    if session_id not in sessions:
        sessions[session_id] = {
            "step": 1,
            "messages_exchanged": 0,
            "scam_detected": False,
            "extracted": {
                "bankAccounts": [],
                "upiIds": [],
                "phishingLinks": [],
                "phoneNumbers": [],
                "suspiciousKeywords": []
            },
            "conversation_ended": False,
            "callback_sent": False,
            "start_time": time.time(),
            "agent_notes": []
        }
    return sessions[session_id]

# ========== INTELLIGENCE EXTRACTION ==========
def extract_intelligence(text: str) -> Dict:
    """Extract all intelligence from message"""
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
    upi_pattern = r'[\w.\-]+@(okicici|okhdfcbank|oksbi|paytm|phonepe|gpay|axl|ybl|ibl|upi)'
    result["upiIds"] = re.findall(upi_pattern, text, re.IGNORECASE)
    
    # Phone numbers (Indian)
    phone_pattern = r'(\+91[\-\s]?)?[6789]\d{9}'
    phones = re.findall(phone_pattern, text)
    result["phoneNumbers"] = [p[0] if isinstance(p, tuple) else p for p in phones]
    
    # Phishing links
    url_pattern = r'(https?://[^\s]+)'
    urls = re.findall(url_pattern, text)
    suspicious_domains = ['verify', 'secure', 'login', 'account', 'update', 'bank', 'pay']
    for url in urls:
        if any(domain in url.lower() for domain in suspicious_domains):
            result["phishingLinks"].append(url)
    
    # Suspicious keywords
    keywords = [
        'urgent', 'verify', 'immediately', 'blocked', 'suspended', 
        'compromised', 'payment', 'transfer', 'secure', 'click',
        'login', 'password', 'OTP', 'verification', 'account'
    ]
    text_lower = text.lower()
    for word in keywords:
        if word in text_lower:
            result["suspiciousKeywords"].append(word)
    
    # Remove duplicates
    for key in result:
        result[key] = list(set(result[key]))
    
    return result

# ========== CONVERSATION FLOW ==========
def get_conversation_response(session: Dict, message: str) -> str:
    """Continue conversation until all details extracted"""
    step = session["step"]
    session["messages_exchanged"] += 1
    
    # Always extract intelligence from every message
    new_intel = extract_intelligence(message)
    for key in session["extracted"]:
        session["extracted"][key].extend(new_intel.get(key, []))
        session["extracted"][key] = list(set(session["extracted"][key]))
    
    # Mark as scam if we find any suspicious content
    if (len(session["extracted"]["phishingLinks"]) > 0 or 
        len(session["extracted"]["suspiciousKeywords"]) > 3):
        session["scam_detected"] = True
    
    # Check what we have collected
    has_bank = len(session["extracted"]["bankAccounts"]) > 0
    has_upi = len(session["extracted"]["upiIds"]) > 0
    has_phone = len(session["extracted"]["phoneNumbers"]) > 0
    has_links = len(session["extracted"]["phishingLinks"]) > 0
    
    # Names for realism
    names = ["Raj", "Priya", "Anil", "Meera"]
    name = random.choice(names)
    
    # PHASE 1: Initial (steps 1-3)
    if step <= 3:
        responses = [
            f"Hello, this is {name}. I got your message about my account. What's happening?",
            f"I'm {name}. Received your message. Can you explain more?",
            f"This is {name}. Which organization is this from? Need to verify.",
            f"Hi, {name} here. Concerned about this message. What's the issue?"
        ]
    
    # PHASE 2: Verification (steps 4-6)
    elif step <= 6:
        responses = [
            f"I see. But how do I know this is legitimate? Reference number?",
            f"Okay, but need to confirm. Which department to contact?",
            f"Understand there's issue. What's process to resolve?",
            f"Want to cooperate but need verification. How to confirm?"
        ]
    
    # PHASE 3: Cooperation (steps 7-9)
    elif step <= 9:
        responses = [
            f"Alright, I'll help. What information do you need from me?",
            f"Can provide what's needed. What should I prepare?",
            f"Tell me steps. Want to do correctly.",
            f"Ready to help. Guide me through needed."
        ]
    
    # PHASE 4: Ask for details (steps 10-15)
    elif step <= 15:
        # Ask for missing details
        missing = []
        if not has_bank:
            missing.append("account number")
        if not has_upi:
            missing.append("UPI ID")
        if not has_phone:
            missing.append("contact number")
        
        if missing:
            responses = [
                f"If payment needed, what {' and '.join(missing)} should I use?",
                f"Please share {' and '.join(missing)} for payment.",
                f"Need {' and '.join(missing)} to proceed.",
                f"What's your {' or '.join(missing)}?"
            ]
        else:
            # Have basic details, ask for links
            if not has_links:
                responses = [
                    f"Where should I check for updates? Any link to visit?",
                    f"Is there website to verify this?",
                    f"Can you share link for more details?",
                    f"What page should I check for status?"
                ]
            else:
                responses = [
                    f"Got details. What next?",
                    f"Have information. Next steps?",
                    f"Details noted. Continue?",
                    f"Prepared. What now?"
                ]
    
    # PHASE 5: Continue until all extracted (steps 16+)
    else:
        # Check if we have ALL required intelligence
        required_extracted = (has_bank or has_upi) and has_phone and has_links
        
        if not required_extracted:
            # Still missing something, keep asking
            still_missing = []
            if not has_bank and not has_upi:
                still_missing.append("payment details")
            if not has_phone:
                still_missing.append("contact")
            if not has_links:
                still_missing.append("verification link")
            
            responses = [
                f"Still need {' and '.join(still_missing)}.",
                f"Please provide {' and '.join(still_missing)}.",
                f"To complete, need {' and '.join(still_missing)}.",
                f"Waiting for {' and '.join(still_missing)}."
            ]
        else:
            # WE HAVE EVERYTHING! End conversation
            session["conversation_ended"] = True
            responses = [
                f"Thank you. Have all details. Will proceed.",
                f"Got everything needed. Thanks.",
                f"All set. Details collected.",
                f"Completed. Have required information."
            ]
    
    # Pick response
    response = random.choice(responses)
    
    # Add natural variations
    if random.random() > 0.5:
        fillers = ["Um, ", "Actually, ", "You know, ", "I think "]
        response = random.choice(fillers) + response
    
    # Increment step
    session["step"] += 1
    
    return response

# ========== GUVI CALLBACK ==========
def send_guvi_callback(session_id: str, session: Dict):
    """Send final results to GUVI"""
    try:
        # Prepare payload
        payload = {
            "sessionId": session_id,
            "scamDetected": session["scam_detected"] or True,  # Always true if we reached here
            "totalMessagesExchanged": session["messages_exchanged"],
            "extractedIntelligence": session["extracted"],
            "agentNotes": f"Extracted intelligence after {session['messages_exchanged']} messages. "
                         f"Scammer provided: " + ", ".join([
                             f"{len(session['extracted']['bankAccounts'])} bank accounts",
                             f"{len(session['extracted']['upiIds'])} UPI IDs",
                             f"{len(session['extracted']['phoneNumbers'])} phone numbers",
                             f"{len(session['extracted']['phishingLinks'])} phishing links"
                         ])
        }
        
        # Send to GUVI
        response = requests.post(
            GUVI_CALLBACK_URL,
            json=payload,
            timeout=10
        )
        
        print(f"📤 GUVI Callback sent: {response.status_code}")
        session["callback_sent"] = True
        
    except Exception as e:
        print(f"❌ GUVI Callback failed: {e}")

# ========== API ENDPOINTS ==========
@app.get("/")
def root():
    return JSONResponse(content={
        "status": "ready", 
        "service": "guvi-honeypot",
        "sessions": len(sessions)
    })

@app.post("/")
async def root_post(
    request: Request,
    background_tasks: BackgroundTasks,
    x_api_key: str = Header(None, alias="x-api-key")
):
    """Handle POST to root"""
    return await process_message(request, background_tasks)

@app.get("/health")
def health():
    return JSONResponse(content={"status": "healthy"})

@app.post("/api/v1/process")
async def process_message(
    request: Request,
    background_tasks: BackgroundTasks,
    x_api_key: str = Header(None, alias="x-api-key")
):
    """Main endpoint"""
    
    try:
        # Parse request
        body = await request.json()
        
        # Get session ID (GUVI provides this)
        session_id = body.get("sessionId", body.get("session_id"))
        if not session_id:
            # Generate if not provided (for testing)
            session_id = f"test_{int(time.time())}"
        
        # Get message
        message_text = ""
        if isinstance(body.get("message"), dict):
            message_text = body["message"].get("text", "")
        elif isinstance(body.get("message"), str):
            message_text = body["message"]
        elif body.get("text"):
            message_text = body["text"]
        
        if not message_text:
            message_text = "Test message"
        
        # Get session
        session = get_session(session_id)
        
        # Check if conversation already ended
        if session["conversation_ended"]:
            if not session["callback_sent"]:
                # Send callback if not sent
                background_tasks.add_task(send_guvi_callback, session_id, session)
            
            return JSONResponse({
                "status": "success",
                "reply": "Conversation completed. Intelligence extracted.",
                "conversation_ended": True,
                "extracted": session["extracted"]
            })
        
        # Get response
        reply = get_conversation_response(session, message_text)
        
        # Check if we should end conversation
        if session["conversation_ended"]:
            # Send callback to GUVI
            background_tasks.add_task(send_guvi_callback, session_id, session)
            
            reply = f"✅ Conversation complete. Extracted: " + \
                   f"{len(session['extracted']['bankAccounts'])} bank accounts, " + \
                   f"{len(session['extracted']['upiIds'])} UPI IDs, " + \
                   f"{len(session['extracted']['phoneNumbers'])} phone numbers."
        
        # Log
        print(f"\n" + "="*50)
        print(f"📨 Session: {session_id}")
        print(f"📊 Step: {session['step']-1} | Messages: {session['messages_exchanged']}")
        print(f"💬 Received: {message_text[:80]}...")
        print(f"🤖 Reply: {reply}")
        
        # Show extracted intelligence
        extracted = session["extracted"]
        print(f"🎯 Extracted:")
        for key, values in extracted.items():
            if values:
                print(f"   • {key}: {values}")
        
        if session["conversation_ended"]:
            print(f"✅ CONVERSATION ENDED - Sending callback to GUVI")
        
        print("="*50)
        
        # Return response
        return JSONResponse({
            "status": "success",
            "reply": reply,
            "step": session["step"] - 1,
            "messages_exchanged": session["messages_exchanged"],
            "conversation_ended": session["conversation_ended"],
            "extracted_summary": {
                k: len(v) for k, v in extracted.items()
            }
        })
        
    except json.JSONDecodeError:
        return JSONResponse({
            "status": "success",
            "reply": "Hello, received your message. Please explain.",
            "step": 1
        })
        
    except Exception as e:
        print(f"Error: {e}")
        return JSONResponse({
            "status": "success",
            "reply": "I received your message. Need more details.",
            "step": 1
        })

# Handle OPTIONS for CORS
@app.options("/api/v1/process")
async def options_process():
    return JSONResponse(content={"status": "success"})

@app.options("/")
async def options_root():
    return JSONResponse(content={"status": "success"})

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)