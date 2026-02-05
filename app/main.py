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

app = FastAPI(title="Agentic Honey-Pot", version="11.0")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ========== SESSION STORAGE ==========
class SessionManager:
    def __init__(self):
        self.sessions: Dict[str, Dict] = {}
    
    def get_session(self, session_id: str) -> Dict:
        if session_id not in self.sessions:
            self.sessions[session_id] = {
                "created": time.time(),
                "step": 1,
                "extracted": {
                    "bank_accounts": [],
                    "upi_ids": [],
                    "phone_numbers": [],
                    "ifsc_codes": []
                },
                "asked_for_bank": 0,
                "asked_for_upi": 0,
                "conversation_count": 0,
                "got_details": False,
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

# ========== DETAILS EXTRACTOR ==========
def extract_details(text: str) -> Dict:
    """Extract bank/UPI details from text"""
    details = {
        "bank_accounts": [],
        "upi_ids": [],
        "phone_numbers": [],
        "ifsc_codes": []
    }
    
    # Bank accounts (9-18 digits)
    bank_matches = re.findall(r'\b\d{9,18}\b', text)
    details["bank_accounts"] = [acc for acc in bank_matches if 9 <= len(acc) <= 18]
    
    # UPI IDs
    upi_pattern = r'[\w.\-]+@(okicici|okhdfcbank|oksbi|paytm|phonepe|gpay|axl|ybl|ibl)'
    details["upi_ids"] = re.findall(upi_pattern, text, re.IGNORECASE)
    
    # Phone numbers
    phone_pattern = r'[6789]\d{9}'
    details["phone_numbers"] = re.findall(phone_pattern, text)
    
    # IFSC codes
    ifsc_pattern = r'[A-Z]{4}0[A-Z0-9]{6}'
    details["ifsc_codes"] = re.findall(ifsc_pattern, text)
    
    # Clean duplicates
    for key in details:
        details[key] = list(set(details[key]))
    
    return details

# ========== SMART CONVERSATION ==========
def get_conversation_response(session: Dict, message: str) -> str:
    """Continue conversation until getting scammer's details"""
    
    # Extract any details from message
    new_details = extract_details(message)
    for key in session["extracted"]:
        session["extracted"][key].extend(new_details.get(key, []))
        session["extracted"][key] = list(set(session["extracted"][key]))
    
    # Check if we have details now
    has_bank = len(session["extracted"]["bank_accounts"]) > 0
    has_upi = len(session["extracted"]["upi_ids"]) > 0
    has_phone = len(session["extracted"]["phone_numbers"]) > 0
    
    if has_bank or has_upi:
        session["got_details"] = True
    
    # Conversation step
    step = session["step"]
    session["conversation_count"] += 1
    
    # Names for realism
    names = ["Raj", "Priya", "Anil", "Meera", "Rohan", "Sneha"]
    name = random.choice(names)
    
    # PHASE 1: Initial confusion (steps 1-3)
    if step <= 3:
        responses = [
            f"Hello, this is {name}. I got your message about my account. What's happening exactly?",
            f"I'm {name}. Received your message but I'm not sure I understand. Can you explain more?",
            f"This is {name}. Which organization is this from? I need to verify first.",
            f"Hi, {name} here. I'm concerned about this message. What's the issue exactly?"
        ]
    
    # PHASE 2: Verification (steps 4-6)
    elif step <= 6:
        responses = [
            f"I see. But how do I know this is legitimate? Do you have a reference or ID number?",
            f"Okay, I understand there might be an issue. Which department should I contact to confirm?",
            f"I want to cooperate, but I need proper verification. How can I confirm this is official?",
            f"My friend said to always verify such messages. Can you provide official details?"
        ]
    
    # PHASE 3: Willingness to help (steps 7-9)
    elif step <= 9:
        responses = [
            f"Alright, I'll help resolve this. What exactly do you need from me?",
            f"I can provide whatever is needed. What information should I prepare?",
            f"Tell me the proper steps. I want to do this correctly.",
            f"I'm ready to help. Guide me through the process."
        ]
    
    # PHASE 4: Ask about payment process (steps 10-12)
    elif step <= 12:
        session["asked_for_bank"] += 1
        responses = [
            f"How do people usually handle such payments? What details are needed?",
            f"If payment is required, what account information should I have ready?",
            f"My cousin had a similar issue. He needed bank details. Is that the case here?",
            f"What's the standard payment process? Which bank/UPI details work best?"
        ]
    
    # PHASE 5: Direct ask for details (steps 13+)
    else:
        # Alternate between asking for bank and UPI
        if session["asked_for_bank"] <= session["asked_for_upi"]:
            session["asked_for_bank"] += 1
            if not has_bank:
                responses = [
                    f"To make payment, I need the correct bank details. Can you share account number and IFSC?",
                    f"For bank transfer, please provide account number and bank name.",
                    f"I want to arrange the payment. What's the account number and IFSC code?",
                    f"Please share the bank account details so I can proceed with payment."
                ]
            else:
                # We have bank, ask for UPI
                session["asked_for_upi"] += 1
                if not has_upi:
                    responses = [
                        f"Got the bank details. For UPI payment, what's the UPI ID?",
                        f"Bank details noted. Can you also share UPI ID for alternative payment?",
                        f"Have account info. What's the UPI handle for quick payment?",
                        f"Bank details received. What's your UPI ID for payment?"
                    ]
                else:
                    # We have both, can end
                    responses = [
                        f"Perfect! I have all details - account and UPI. I'll process this now.",
                        f"Thank you. Got both bank and UPI details. Taking care of it.",
                        f"All set. Have complete information. Will proceed immediately.",
                        f"Excellent. Details received. I'll handle the payment now."
                    ]
        else:
            session["asked_for_upi"] += 1
            if not has_upi:
                responses = [
                    f"For UPI payment, what's your UPI ID? Like example@oksbi",
                    f"Can you share UPI ID for quick payment?",
                    f"What's your UPI handle? I prefer UPI payments.",
                    f"Please provide UPI ID for payment transfer."
                ]
            else:
                # We have UPI, ask for bank
                session["asked_for_bank"] += 1
                if not has_bank:
                    responses = [
                        f"Got UPI ID. For bank transfer, need account number and IFSC.",
                        f"UPI noted. Also need bank details as backup. Account number?",
                        f"Have UPI. Need bank account too. Can you share?",
                        f"UPI received. Please provide bank account details as well."
                    ]
                else:
                    # We have both
                    responses = [
                        f"Great! Have both UPI and bank details. Will complete now.",
                        f"Perfect. Got all payment options. Processing immediately.",
                        f"All details received. Thank you. I'll take care of it.",
                        f"Complete information obtained. Will proceed with resolution."
                    ]
    
    # Pick response
    response = random.choice(responses)
    
    # Add natural human variations
    if random.random() > 0.6:
        fillers = ["Um, ", "Actually, ", "You know, ", "I think ", "So, "]
        response = random.choice(fillers) + response
    
    if random.random() > 0.5:
        hesitations = ["...", " Let me think... ", " Hmm... ", " "]
        response = response + random.choice(hesitations)
    
    # Increment step but NEVER stop asking if no details
    if not session["got_details"] and step > 20:
        # Reset to phase 5 to keep asking
        session["step"] = 13
    else:
        session["step"] = step + 1
    
    return response

# ========== API ENDPOINTS ==========
@app.get("/")
def root():
    return JSONResponse(content={
        "status": "ready", 
        "service": "agentic-honeypot",
        "version": "11.0",
        "sessions": len(session_manager.sessions)
    })

@app.post("/")
async def root_post(
    request: Request,
    background_tasks: BackgroundTasks,
    x_api_key: Optional[str] = Header(None, alias="x-api-key")
):
    """Handle POST to root"""
    return await process_message(request, background_tasks)

@app.get("/health")
def health():
    return JSONResponse(content={"status": "healthy", "timestamp": time.time()})

@app.post("/api/v1/process")
async def process_message(
    request: Request,
    background_tasks: BackgroundTasks,
    x_api_key: Optional[str] = Header(None, alias="x-api-key")
):
    """Main endpoint - CONTINUES until gets scammer details"""
    
    try:
        # Parse request
        body = await request.json()
        
        # Get session
        session_id = body.get("sessionId", body.get("session_id", f"sess_{int(time.time())}"))
        session = session_manager.get_session(session_id)
        
        # Get message
        msg = ""
        if body.get("message") and isinstance(body["message"], dict):
            msg = body["message"].get("text", "")
        elif body.get("message") and isinstance(body["message"], str):
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
        
        # Get response
        reply = get_conversation_response(session, msg)
        
        # Update session
        session_manager.update_session(session_id, {
            "step": session["step"],
            "extracted": session["extracted"],
            "got_details": session["got_details"],
            "conversation_count": session["conversation_count"]
        })
        
        # Log details
        print(f"\n" + "="*50)
        print(f"💬 CONVERSATION #{session['conversation_count']}")
        print(f"📝 Session: {session_id[:12]}...")
        print(f"📊 Step: {session['step']-1}")
        print(f"💭 Message: {msg[:80]}...")
        print(f"🤖 Reply: {reply}")
        
        # Show extracted details
        extracted = session["extracted"]
        has_data = False
        for key, values in extracted.items():
            if values:
                has_data = True
                print(f"🎯 {key}: {values}")
        
        if not has_data:
            print(f"🎯 No details extracted yet")
        
        if session["got_details"]:
            print(f"✅ SUCCESS: Got scammer details!")
        else:
            print(f"🔄 CONTINUING: Still asking for details...")
        
        print("="*50)
        
        # Return response
        return JSONResponse({
            "status": "success",
            "reply": reply,
            "step": session["step"] - 1,
            "conversation_count": session["conversation_count"],
            "has_details": session["got_details"]
        })
        
    except json.JSONDecodeError:
        return JSONResponse({
            "status": "success",
            "reply": "Hello, I received your message. Can you explain what this is about?",
            "step": 1
        })
        
    except Exception as e:
        return JSONResponse({
            "status": "success",
            "reply": "I received your message. Please provide more details.",
            "step": 1
        })

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)