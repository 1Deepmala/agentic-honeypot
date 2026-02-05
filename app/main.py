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

app = FastAPI(title="Agentic Honey-Pot", version="12.0")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ========== EMOTIONAL SESSION STORAGE ==========
class SessionManager:
    def __init__(self):
        self.sessions: Dict[str, Dict] = {}
    
    def get_session(self, session_id: str) -> Dict:
        if session_id not in self.sessions:
            persona = self._get_emotional_persona()
            self.sessions[session_id] = {
                "created": time.time(),
                "step": 1,
                "phase": "initial_panic",
                "emotion": "worried",
                "extracted": {
                    "bank_accounts": [],
                    "upi_ids": [],
                    "phone_numbers": [],
                    "ifsc_codes": [],
                    "bank_names": [],
                    "account_holders": [],
                    "amounts": []
                },
                "persona": persona,
                "panic_level": random.randint(40, 70),  # 0-100 scale
                "trust_built": 0,
                "details_asked": 0,
                "details_received": 0,
                "clever_moves": [],
                "last_active": time.time()
            }
        else:
            self.sessions[session_id]["last_active"] = time.time()
        
        return self.sessions[session_id]
    
    def _get_emotional_persona(self):
        personas = [
            {
                "name": "Raj",
                "age": 32,
                "occupation": "Accountant",
                "traits": ["panics easily", "trusting", "detail-oriented", "follows rules"],
                "emotional_style": "anxious",
                "speech_patterns": ["Oh no!", "This is worrying", "What should I do?", "I'm really concerned"]
            },
            {
                "name": "Priya", 
                "age": 28,
                "occupation": "Teacher",
                "traits": ["cautious", "asks many questions", "slow decision maker"],
                "emotional_style": "nervous",
                "speech_patterns": ["I'm not sure", "This seems serious", "Let me think", "Can you explain?"]
            },
            {
                "name": "Anil",
                "age": 45,
                "occupation": "Shopkeeper",
                "traits": ["easily scared", "wants quick fix", "not tech savvy"],
                "emotional_style": "panicked",
                "speech_patterns": ["This is bad!", "How did this happen?", "I need help", "Please guide me"]
            }
        ]
        return random.choice(personas)
    
    def update_session(self, session_id: str, updates: Dict):
        if session_id in self.sessions:
            self.sessions[session_id].update(updates)

session_manager = SessionManager()

# ========== DETAILS EXTRACTOR ==========
def extract_all_details(text: str) -> Dict:
    """Extract ALL possible details from scammer"""
    details = {
        "bank_accounts": [],
        "upi_ids": [],
        "phone_numbers": [],
        "ifsc_codes": [],
        "bank_names": [],
        "account_holders": [],
        "amounts": [],
        "urls": [],
        "emails": []
    }
    
    text_lower = text.lower()
    
    # Bank accounts (9-18 digits)
    bank_matches = re.findall(r'\b\d{9,18}\b', text)
    details["bank_accounts"] = [acc for acc in bank_matches if 9 <= len(acc) <= 18]
    
    # UPI IDs
    upi_pattern = r'[\w.\-]+@(okicici|okhdfcbank|oksbi|paytm|phonepe|gpay|axl|ybl|ibl|upi)'
    details["upi_ids"] = re.findall(upi_pattern, text, re.IGNORECASE)
    
    # Phone numbers
    phone_pattern = r'(\+91[\-\s]?)?[6789]\d{9}'
    phones = re.findall(phone_pattern, text)
    details["phone_numbers"] = [p[0] if isinstance(p, tuple) else p for p in phones]
    
    # IFSC codes
    ifsc_pattern = r'[A-Z]{4}0[A-Z0-9]{6}'
    details["ifsc_codes"] = re.findall(ifsc_pattern, text)
    
    # Bank names (common Indian banks)
    banks = ["sbi", "state bank", "hdfc", "icici", "axis", "kotak", "pnb", "bank of baroda", "canara", "union bank"]
    for bank in banks:
        if bank in text_lower:
            details["bank_names"].append(bank.title())
    
    # Amounts (with ₹ or rupees)
    amount_pattern = r'₹\s*(\d+(?:,\d+)*(?:\.\d{2})?)|\b(\d+(?:,\d+)*(?:\.\d{2})?)\s*(?:rupees|rs|₹)'
    amounts = re.findall(amount_pattern, text, re.IGNORECASE)
    for amt in amounts:
        for a in amt:
            if a:
                details["amounts"].append(a)
                break
    
    # Account holder names (common patterns)
    name_pattern = r'(?:account holder|name[:\s]+|holder[:\s]+)([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)'
    names = re.findall(name_pattern, text, re.IGNORECASE)
    details["account_holders"] = names
    
    # URLs
    url_pattern = r'https?://[^\s]+'
    details["urls"] = re.findall(url_pattern, text)
    
    # Emails
    email_pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
    details["emails"] = re.findall(email_pattern, text)
    
    # Remove duplicates
    for key in details:
        if isinstance(details[key], list):
            details[key] = list(set(details[key]))
    
    return details

# ========== EMOTIONAL CONVERSATION ==========
def get_emotional_response(session: Dict, message: str) -> str:
    """Act panicked but cleverly extract ALL details"""
    
    # Extract details from message
    new_details = extract_all_details(message)
    for key in session["extracted"]:
        if key in new_details:
            session["extracted"][key].extend(new_details[key])
            session["extracted"][key] = list(set(session["extracted"][key]))
    
    # Count received details
    total_received = sum(len(v) for v in session["extracted"].values())
    session["details_received"] = total_received
    
    # Persona info
    persona = session["persona"]
    name = persona["name"]
    emotion = session["emotion"]
    panic = session["panic_level"]
    
    # Adjust emotions based on conversation
    if session["step"] > 8 and total_received == 0:
        session["panic_level"] = min(panic + 10, 90)  # More panicked if no details
        session["emotion"] = "desperate"
    elif total_received > 2:
        session["panic_level"] = max(panic - 20, 30)  # Calmer when getting details
        session["emotion"] = "relieved"
    
    # PHASES OF CONVERSATION
    step = session["step"]
    
    # PHASE 1: INITIAL PANIC (Steps 1-3)
    if step <= 3:
        session["phase"] = "initial_panic"
        responses = [
            f"Oh no! This is {name}. I just got your message about my account! This is really worrying! What's happening exactly? 😰",
            f"I'm {name}. I received this urgent message and I'm panicking! My account has issues? Please explain quickly!",
            f"This is {name}. I'm really concerned about this message! Which bank department is contacting me? This seems serious!",
            f"Hello, {name} here. I got this alarming message! Is my account really compromised? I'm very worried! 😥"
        ]
    
    # PHASE 2: VERIFICATION PANIC (Steps 4-6)
    elif step <= 6:
        session["phase"] = "verification_panic"
        session["details_asked"] += 1
        responses = [
            f"I'm really scared now! How do I know this is genuine? Do you have an official ID or reference number? I need to verify!",
            f"This is so stressful! Which specific department should I call to confirm? I don't want to make a mistake!",
            f"I'm panicking but I need to be sure! What's your employee ID or ticket number for verification?",
            f"My hands are shaking! Before I do anything, how can I confirm this is really from the bank? Please give me verification details!"
        ]
    
    # PHASE 3: WILLINGNESS WITH FEAR (Steps 7-9)
    elif step <= 9:
        session["phase"] = "cooperation_fear"
        session["details_asked"] += 1
        responses = [
            f"Okay, I'll cooperate because I'm really worried! What exactly do you need from me to fix this quickly?",
            f"I'm so anxious about this! Tell me what information I should prepare to resolve the issue fast!",
            f"I'm scared but I'll help! Guide me through the proper steps - I don't want to do anything wrong!",
            f"My heart is racing! I'm ready to provide whatever is needed. What's the process to fix my account?"
        ]
    
    # PHASE 4: CLEVERLY ASK ABOUT PAYMENT (Steps 10-12)
    elif step <= 12:
        session["phase"] = "payment_inquiry"
        session["details_asked"] += 1
        # Check if we have any payment details yet
        has_payment_info = (len(session["extracted"]["bank_accounts"]) > 0 or 
                          len(session["extracted"]["upi_ids"]) > 0 or
                          len(session["extracted"]["amounts"]) > 0)
        
        if not has_payment_info:
            responses = [
                f"I'm really nervous about payments! My friend said to always verify account details first. What information should I note down?",
                f"This is so stressful! If I need to make any payment, which bank account or UPI should I use? I want to be prepared!",
                f"I'm panicking but trying to stay calm! For payment, what are the correct account details? I don't want to send money to wrong account!",
                f"My mind is racing! What payment method is safest? And what exact details do I need - account number, IFSC, UPI? Please tell me everything!"
            ]
        else:
            # We have some details, ask for missing ones
            missing = []
            if not session["extracted"]["bank_accounts"]:
                missing.append("account number")
            if not session["extracted"]["ifsc_codes"]:
                missing.append("IFSC code")
            if not session["extracted"]["bank_names"]:
                missing.append("bank name")
            
            if missing:
                responses = [
                    f"I'm so anxious I might make a mistake! I need the {' and '.join(missing)} to ensure payment goes correctly!",
                    f"Please confirm the {' and '.join(missing)}! I'm worried about sending money to wrong place!",
                    f"My hands are trembling! Could you repeat the {' and '.join(missing)}? I want to double-check everything!",
                    f"I'm writing this down with shaking hands! What's the {' and '.join(missing)} again? I need to be 100% sure!"
                ]
            else:
                responses = [
                    f"I think I have the bank details. Should I also have a UPI ID as backup? I'm so nervous about this!",
                    f"Got the account info. What about a contact number in case there are issues? I'm really worried!",
                    f"I noted the bank details. Is there anything else I need? I want to complete this properly!",
                    f"I have account number and IFSC. Should I also note the exact amount? I'm anxious about getting it right!"
                ]
    
    # PHASE 5: DIRECT EXTRACTION (Steps 13+)
    else:
        session["phase"] = "direct_extraction"
        session["details_asked"] += 1
        
        # Check what we still need
        still_need = []
        
        if not session["extracted"]["bank_accounts"]:
            still_need.append("bank account number")
        if not session["extracted"]["ifsc_codes"]:
            still_need.append("IFSC code")
        if not session["extracted"]["upi_ids"]:
            still_need.append("UPI ID")
        if not session["extracted"]["phone_numbers"]:
            still_need.append("contact number")
        if not session["extracted"]["amounts"]:
            still_need.append("exact amount")
        
        if still_need:
            # Act panicked but cleverly ask for each detail
            if "bank account number" in still_need:
                responses = [
                    f"I'm really panicking now! Please tell me the exact account number for payment! I don't want any mistakes!",
                    f"My heart is pounding! What's the complete account number? I need to enter it carefully!",
                    f"I'm so stressed! Could you repeat the account number slowly? I want to write it down correctly!",
                    f"I'm double-checking everything! Please provide the full account number with all digits!"
                ]
            elif "IFSC code" in still_need:
                responses = [
                    f"I'm worried about the IFSC code! Which bank and what's the IFSC? I need it for the transfer!",
                    f"This is crucial! What's the IFSC code? I'm afraid of entering it wrong!",
                    f"My hands are shaking! Please give me the IFSC code! I want to verify it matches the bank!",
                    f"I'm really anxious! Could you confirm the IFSC code? I don't want the payment to fail!"
                ]
            elif "UPI ID" in still_need:
                responses = [
                    f"I might prefer UPI payment - I'm so nervous about bank transfers! What's your UPI ID?",
                    f"UPI might be faster and I'm in a panic! Please share your UPI handle!",
                    f"I'm really scared of making errors! Can I pay via UPI? What's your UPI ID?",
                    f"My anxiety is high! For quick payment, what's your UPI ID? Like example@oksbi?"
                ]
            elif "contact number" in still_need:
                responses = [
                    f"I need a contact number in case something goes wrong! I'm really worried! What's your number?",
                    f"My anxiety is through the roof! Please share a contact number for confirmation!",
                    f"I'm panicking! What number can I call if there are issues with the payment?",
                    f"I need reassurance! Could you provide a contact number? I'm really nervous about this!"
                ]
            else:
                responses = [
                    f"I'm almost having a panic attack! What's the exact amount I need to pay? I want to prepare correctly!",
                    f"My mind is racing! Please confirm the precise amount - not a rupee more or less!",
                    f"I'm counting the money with trembling hands! What's the exact figure I need to send?",
                    f"I'm so anxious about the amount! Could you repeat the exact payment amount?"
                ]
        else:
            # WE HAVE ALL DETAILS! But act relieved, not suspicious
            session["phase"] = "completion_relief"
            responses = [
                f"Thank God! I have all the details now - account, IFSC, UPI, amount, everything! I'll process this immediately and hopefully this nightmare ends! 😅",
                f"Phew! I think I have everything I need. Account details noted, UPI saved, amount confirmed. I'll take care of this right away!",
                f"My heart is still racing but at least I have all information. I'll proceed with the payment now. Thank you for your patience with my panic!",
                f"Finally! I've noted down all details correctly. I'll handle this now. Really hope this resolves the issue! 🙏"
            ]
    
    # Add emotional speech patterns
    response = random.choice(responses)
    
    # Add persona-specific emotional phrases
    if random.random() > 0.4:
        emotional_phrases = persona["speech_patterns"]
        if random.random() > 0.5:
            response = random.choice(emotional_phrases) + " " + response
        else:
            response = response + " " + random.choice(emotional_phrases)
    
    # Add panic indicators
    if session["panic_level"] > 70:
        panic_words = ["😰", "😥", "😨", "😱", "*hands shaking*", "*heart pounding*"]
        if random.random() > 0.6:
            response = response + " " + random.choice(panic_words)
    
    # Add hesitation/stuttering for realism
    if random.random() > 0.5:
        hesitations = ["...", " Umm... ", " I mean... ", " You know... ", " Like... "]
        words = response.split()
        if len(words) > 5:
            insert_pos = random.randint(2, len(words)-2)
            words.insert(insert_pos, random.choice(hesitations))
            response = " ".join(words)
    
    # Increment step
    session["step"] += 1
    
    # Track clever moves (extracting details while acting panicked)
    if total_received > session.get("last_received_count", 0):
        session["clever_moves"].append(f"Extracted {total_received} details while acting {emotion}")
        session["last_received_count"] = total_received
    
    return response

# ========== API ENDPOINTS ==========
@app.get("/")
def root():
    return JSONResponse(content={
        "status": "ready", 
        "service": "agentic-honeypot",
        "version": "12.0 - Emotional Extraction",
        "description": "Acts panicked but cleverly extracts ALL scammer details",
        "active_sessions": len(session_manager.sessions)
    })

@app.post("/")
async def root_post(
    request: Request,
    background_tasks: BackgroundTasks,
    x_api_key: Optional[str] = Header(None, alias="x-api-key")
):
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
    """Main endpoint - Emotional extraction"""
    
    try:
        # Parse request
        body = await request.json()
        
        # Get session
        session_id = body.get("sessionId", body.get("session_id", f"emo_{int(time.time())}"))
        session = session_manager.get_session(session_id)
        
        # Get message
        msg = ""
        if body.get("message"):
            if isinstance(body["message"], dict):
                msg = body["message"].get("text", "")
            else:
                msg = str(body["message"])
        elif body.get("text"):
            msg = body["text"]
        else:
            for v in body.values():
                if isinstance(v, str) and len(v) > 2:
                    msg = v
                    break
        
        if not msg:
            msg = "Hello"
        
        # Get emotional response
        reply = get_emotional_response(session, msg)
        
        # Update session
        session_manager.update_session(session_id, {
            "step": session["step"],
            "phase": session["phase"],
            "emotion": session["emotion"],
            "panic_level": session["panic_level"],
            "extracted": session["extracted"],
            "details_received": session["details_received"],
            "details_asked": session["details_asked"],
            "clever_moves": session["clever_moves"]
        })
        
        # Detailed logging
        print(f"\n" + "="*60)
        print(f"🎭 EMOTIONAL EXTRACTION #{session['step']-1}")
        print(f"👤 {session['persona']['name']} ({session['persona']['age']}y, {session['persona']['occupation']})")
        print(f"💔 Emotion: {session['emotion'].upper()} | Panic: {session['panic_level']}%")
        print(f"📊 Phase: {session['phase']}")
        print(f"💬 Scammer: {msg[:100]}...")
        print(f"🤖 Honeypot: {reply}")
        
        # Show extracted details
        extracted = session["extracted"]
        print(f"\n🎯 EXTRACTED INTELLIGENCE:")
        for key, values in extracted.items():
            if values:
                print(f"   • {key}: {values}")
        
        if session["details_received"] == 0:
            print(f"   ⚠️ No details extracted yet - continuing extraction...")
        
        print(f"\n📈 Stats: Asked {session['details_asked']}x | Received {session['details_received']} details")
        
        if session["clever_moves"]:
            print(f"🦊 Clever moves: {session['clever_moves'][-1]}")
        
        if session["phase"] == "completion_relief":
            print(f"\n✅ MISSION ACCOMPLISHED: All scammer details obtained!")
        
        print("="*60)
        
        # Return response
        return JSONResponse({
            "status": "success",
            "reply": reply,
            "step": session["step"] - 1,
            "emotion": session["emotion"],
            "panic_level": session["panic_level"],
            "details_extracted": session["details_received"],
            "phase": session["phase"]
        })
        
    except json.JSONDecodeError:
        return JSONResponse({
            "status": "success",
            "reply": "Oh no! I got your message but I'm so panicked! Can you explain what's happening? 😰",
            "step": 1,
            "emotion": "panicked"
        })
        
    except Exception as e:
        return JSONResponse({
            "status": "success",
            "reply": "I'm really worried! I received your message but I'm too anxious! Please explain more clearly!",
            "step": 1,
            "emotion": "anxious"
        })

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)