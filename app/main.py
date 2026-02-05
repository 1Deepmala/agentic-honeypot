from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import re
import time
import random

app = FastAPI()

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Session storage
sessions = {}

# Emotional phrases (generic - no personal info)
EMOTIONS = {
    "panic": [
        "Oh no! This is really worrying me!",
        "I'm getting really anxious about this!",
        "This is making me panic!",
        "My heart is racing just thinking about this!",
        "I'm so stressed right now!",
        "This has me really scared!",
        "I'm feeling really nervous about this!"
    ],
    "confusion": [
        "Sorry, I'm a bit confused...",
        "Can you explain that again?",
        "I don't fully understand...",
        "Wait, let me make sure I get this...",
        "I'm not sure I'm following..."
    ],
    "cooperation": [
        "I want to cooperate to fix this...",
        "Let me help resolve this issue...",
        "I'll do whatever is needed...",
        "Tell me how I can help...",
        "I want to get this sorted out..."
    ],
    "trust": [
        "Thank you for explaining...",
        "I appreciate you helping me with this...",
        "You're being very clear...",
        "This is making more sense now...",
        "I feel better understanding this..."
    ]
}

def extract_details(text):
    """Extract scammer's details only"""
    details = {
        "phone_numbers": [],      # Scammer's phone
        "bank_accounts": [],      # Scammer's bank account
        "ifsc_codes": [],         # Scammer's IFSC
        "upi_ids": [],            # Scammer's UPI
        "phishing_links": []      # Scammer's links
    }
    
    # Phone: 10 digits, starts with 6-9 (scammer's number)
    phones = re.findall(r'\b[6789]\d{9}\b', text)
    details["phone_numbers"] = [p for p in phones if len(p) == 10]
    
    # Bank accounts: 11-18 digits (scammer's account)
    banks = re.findall(r'\b\d{11,18}\b', text)
    details["bank_accounts"] = [b for b in banks if not re.match(r'^[6789]', b) or len(b) > 10]
    
    # IFSC codes (scammer's bank)
    ifscs = re.findall(r'\b[A-Z]{4}0[0-9A-Z]{6}\b', text.upper())
    details["ifsc_codes"] = ifscs
    
    # UPI IDs (scammer's UPI)
    upis = re.findall(r'[\w.\-]+@(okicici|okhdfcbank|oksbi|paytm|phonepe|gpay|axl|ybl|ibl|sbi|hdfc|icici|axis)', text, re.I)
    details["upi_ids"] = upis
    
    # Phishing links (scammer's links)
    links = re.findall(r'https?://[^\s]+', text)
    suspicious = ['verify', 'secure', 'login', 'account', 'bank', 'pay', 'update', 'click', 'secure']
    details["phishing_links"] = [l for l in links if any(s in l.lower() for s in suspicious)]
    
    # Remove duplicates
    for key in details:
        details[key] = list(set(details[key]))
    
    return details

def get_response(session, message):
    """Smart woman - doesn't give her details, only extracts scammer's details"""
    step = session["step"]
    
    # Extract scammer's details from message
    new_details = extract_details(message)
    for key in session["scammer_details"]:
        session["scammer_details"][key].extend(new_details.get(key, []))
        session["scammer_details"][key] = list(set(session["scammer_details"][key]))
    
    # Check what scammer details we have collected
    has_phone = len(session["scammer_details"]["phone_numbers"]) > 0
    has_bank = len(session["scammer_details"]["bank_accounts"]) > 0
    has_upi = len(session["scammer_details"]["upi_ids"]) > 0
    has_ifsc = len(session["scammer_details"]["ifsc_codes"]) > 0
    has_link = len(session["scammer_details"]["phishing_links"]) > 0
    
    # Check if we have ALL scammer details
    has_all_scammer_details = (has_bank or has_upi) and has_phone and has_ifsc and has_link
    
    # Emotional state (varies by step)
    if step < 4:
        emotion = "panic"
    elif step < 8:
        emotion = "confusion"
    elif step < 12:
        emotion = "cooperation"
    else:
        emotion = "trust"
    
    # Add emotional phrase (70% chance)
    emotional_phrase = ""
    if random.random() > 0.3:
        emotional_phrase = random.choice(EMOTIONS[emotion]) + " "
    
    # Human-like filler words
    filler = random.choice(["Um, ", "Actually, ", "You know, ", "I think ", ""])
    
    # Step 1-3: Initial panic (doesn't give any personal info)
    if step == 1:
        reply = f"{filler}{emotional_phrase}I just got your message about my account! This is really worrying me! What's happening exactly?"
    
    elif step == 2:
        reply = f"{filler}{emotional_phrase}I'm really concerned about this! How do I know this is genuine? Do you have any reference number?"
    
    elif step == 3:
        reply = f"{filler}{emotional_phrase}This is making me really anxious! Which organization is this from? I need to be sure!"
    
    # Step 4-6: Confusion but willing to cooperate
    elif step == 4:
        reply = f"{filler}{emotional_phrase}Okay, I understand there might be an issue. What exactly do you need from me to fix this?"
    
    elif step == 5:
        reply = f"{filler}{emotional_phrase}I want to cooperate to resolve this. What information should I prepare?"
    
    elif step == 6:
        reply = f"{filler}{emotional_phrase}Tell me the proper steps. I want to do this correctly but I'm really nervous!"
    
    # Step 7-9: Smartly ask about payment process (to get scammer's details)
    elif step == 7:
        reply = f"{filler}{emotional_phrase}If payment is needed, what payment method should I use? And what details do I need to note down?"
    
    elif step == 8:
        # Check if we have payment details yet
        if not has_bank and not has_upi:
            reply = f"{filler}{emotional_phrase}For the payment, what account number or UPI ID should I use? I want to be prepared."
        else:
            if has_bank:
                acc = session["scammer_details"]["bank_accounts"][0]
                reply = f"{filler}{emotional_phrase}I see. For account {acc}, what's the IFSC code? I need it for the transfer."
            else:
                reply = f"{filler}{emotional_phrase}Got it. For UPI payment, what's the associated bank account? Just in case."
    
    elif step == 9:
        if not has_phone:
            reply = f"{filler}{emotional_phrase}What's a contact number I can use if I have questions during the payment?"
        else:
            reply = f"{filler}{emotional_phrase}Phone number noted. I also need the IFSC code to be sure."
    
    # Step 10-12: Ask for remaining details
    elif step == 10:
        if not has_ifsc:
            reply = f"{filler}{emotional_phrase}Please share the IFSC code. I'm worried about entering it wrong!"
        else:
            reply = f"{filler}{emotional_phrase}IFSC noted. Is there a website or link where I can check the status?"
    
    elif step == 11:
        if not has_link:
            reply = f"{filler}{emotional_phrase}Can you share a link for verification? I want to make sure everything is correct."
        else:
            # Check what's still missing
            missing = []
            if not has_bank and not has_upi:
                missing.append("payment details")
            if not has_phone:
                missing.append("contact number")
            
            if missing:
                reply = f"{filler}{emotional_phrase}I still need {' and '.join(missing)} to proceed."
            else:
                reply = f"{filler}{emotional_phrase}Almost done. Just confirming everything is correct."
    
    # Step 12+: Keep asking until we have ALL scammer details
    else:
        if not has_all_scammer_details:
            # Ask for specific missing scammer details
            missing = []
            if not has_bank and not has_upi:
                missing.append("account number or UPI ID")
            if not has_phone:
                missing.append("contact number")
            if not has_ifsc:
                missing.append("IFSC code")
            if not has_link:
                missing.append("verification link")
            
            reply = f"{filler}{emotional_phrase}To feel secure about this, I need {' and '.join(missing)}. Can you please provide?"
        else:
            # WE HAVE ALL SCAMMER DETAILS! End naturally
            reply = f"{filler}Thank you for all the information! I have everything I need now. I'll take care of this right away."
            session["conversation_active"] = False
    
    # Sometimes add hesitation for realism
    if random.random() > 0.6:
        hesitations = ["...", " Let me think... ", " Hmm... ", " You know... "]
        reply = reply + random.choice(hesitations)
    
    # Increment step
    session["step"] = min(step + 1, 20)
    
    return reply, has_all_scammer_details

@app.get("/")
def root():
    return JSONResponse({"status": "ready", "sessions": len(sessions)})

@app.get("/health")
def health():
    return JSONResponse({"status": "healthy", "timestamp": time.time()})

@app.post("/")
async def handle(request: Request):
    try:
        data = await request.json()
        
        # Get session ID (from GUVI)
        session_id = data.get("sessionId", data.get("session_id", f"session_{int(time.time())}"))
        
        # Get message
        msg = data.get("text") or data.get("message") or ""
        if isinstance(msg, dict):
            msg = msg.get("text", "")
        
        if not msg:
            msg = "Hello"
        
        # Initialize session
        if session_id not in sessions:
            sessions[session_id] = {
                "step": 1,
                "messages": 0,
                "scammer_details": {  # ONLY stores scammer's details
                    "phone_numbers": [],
                    "bank_accounts": [],
                    "ifsc_codes": [],
                    "upi_ids": [],
                    "phishing_links": []
                },
                "conversation_active": True,
                "start_time": time.time()
            }
        
        session = sessions[session_id]
        session["messages"] += 1
        
        # Get smart response (doesn't give her details)
        reply, has_all = get_response(session, msg)
        
        # Log conversation
        print(f"\n" + "="*60)
        print(f"🎭 SMART WOMAN HONEYPOT")
        print(f"📨 Session: {session_id[:12]} | Step: {session['step']-1}")
        print(f"💬 Scammer said: {msg[:80]}...")
        print(f"🤖 Woman replied: {reply}")
        
        # Show extracted SCAMMER details
        scammer = session["scammer_details"]
        print(f"\n🎯 EXTRACTED SCAMMER DETAILS:")
        
        if scammer["phone_numbers"]:
            print(f"   📱 Scammer's Phone: {scammer['phone_numbers']}")
        else:
            print(f"   📱 Scammer's Phone: Not yet (looking for 10-digit number)")
        
        if scammer["bank_accounts"]:
            print(f"   💳 Scammer's Bank Account: {scammer['bank_accounts']}")
        else:
            print(f"   💳 Scammer's Bank Account: Not yet (looking for 11-18 digits)")
        
        if scammer["ifsc_codes"]:
            print(f"   🏦 Scammer's IFSC: {scammer['ifsc_codes']}")
        else:
            print(f"   🏦 Scammer's IFSC: Not yet (looking for ABCD0123456)")
        
        if scammer["upi_ids"]:
            print(f"   🔄 Scammer's UPI: {scammer['upi_ids']}")
        else:
            print(f"   🔄 Scammer's UPI: Not yet (looking for name@bank)")
        
        if scammer["phishing_links"]:
            print(f"   🔗 Scammer's Links: {scammer['phishing_links']}")
        else:
            print(f"   🔗 Scammer's Links: Not yet (looking for http/https)")
        
        if has_all:
            print(f"\n✅ MISSION ACCOMPLISHED! Got ALL scammer details!")
            print(f"   The woman acted scared but cleverly extracted everything.")
        else:
            print(f"\n🔄 CONTINUING... Still need more scammer details.")
        
        print("="*60)
        
        return JSONResponse({
            "status": "success",
            "reply": reply,
            "step": session["step"] - 1,
            "messages_exchanged": session["messages"],
            "conversation_active": session["conversation_active"],
            "scammer_details_extracted": {
                "phone_numbers": len(scammer["phone_numbers"]),
                "bank_accounts": len(scammer["bank_accounts"]),
                "ifsc_codes": len(scammer["ifsc_codes"]),
                "upi_ids": len(scammer["upi_ids"]),
                "phishing_links": len(scammer["phishing_links"])
            }
        })
        
    except Exception as e:
        print(f"Error: {e}")
        return JSONResponse({
            "status": "success",
            "reply": "Hello, I received your message. I'm a bit concerned - can you explain what this is about?",
            "step": 1,
            "conversation_active": True
        })

if __name__ == "__main__":
    import uvicorn
    import os
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)