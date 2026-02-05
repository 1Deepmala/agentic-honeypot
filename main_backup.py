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

# Simple storage
sessions = {}

# Emotional phrases
EMOTIONS = {
    "worried": ["I'm really worried...", "This is concerning...", "I'm anxious about this..."],
    "confused": ["I don't understand...", "Can you explain?", "I'm confused..."],
    "helpful": ["I want to help...", "Let me cooperate...", "I'll do what's needed..."]
}

def extract_intelligence(text):
    """Extract SPECIFIC intelligence as per GUVI requirements"""
    intel = {
        "phone_numbers": [],      # 10 digit numbers (scammer's phone)
        "bank_accounts": [],      # >10 digit bank accounts
        "ifsc_codes": [],         # IFSC codes
        "upi_ids": [],            # UPI IDs like name@bank
        "phishing_links": []      # http/https links
    }
    
    text_lower = text.lower()
    
    # 1. PHONE NUMBERS: Exactly 10 digits, starts with 6-9
    phone_pattern = r'\b[6789]\d{9}\b'
    phones = re.findall(phone_pattern, text)
    intel["phone_numbers"] = [p for p in phones if len(p) == 10]
    
    # 2. BANK ACCOUNTS: More than 10 digits (11-18 digits)
    bank_pattern = r'\b\d{11,18}\b'
    banks = re.findall(bank_pattern, text)
    # Filter out phone numbers that might match
    intel["bank_accounts"] = [b for b in banks if not re.match(r'^[6789]', b) or len(b) > 10]
    
    # 3. IFSC CODES: 4 letters + 0 + 6 alphanumeric
    ifsc_pattern = r'\b[A-Z]{4}0[0-9A-Z]{6}\b'
    intel["ifsc_codes"] = re.findall(ifsc_pattern, text.upper())
    
    # 4. UPI IDs: name@bank
    upi_pattern = r'\b[\w.\-]+@(okicici|okhdfcbank|oksbi|paytm|phonepe|gpay|axl|ybl|ibl|sbi|hdfc|icici|axis|kotak|yesbank|upi)\b'
    intel["upi_ids"] = re.findall(upi_pattern, text_lower)
    
    # 5. PHISHING LINKS: http/https URLs
    link_pattern = r'https?://[^\s]+'
    links = re.findall(link_pattern, text)
    # Filter for suspicious domains
    suspicious_keywords = ['verify', 'secure', 'login', 'account', 'update', 'bank', 'pay', 'wallet']
    intel["phishing_links"] = [link for link in links if any(keyword in link.lower() for keyword in suspicious_keywords)]
    
    # Remove duplicates
    for key in intel:
        intel[key] = list(set(intel[key]))
    
    return intel

def get_response(session, message):
    """Human-like conversation that extracts SPECIFIC details"""
    step = session["step"]
    name = random.choice(["Raj", "Priya", "Anil", "Meera"])
    
    # Extract intelligence
    new_intel = extract_intelligence(message)
    for key in session["intel"]:
        session["intel"][key].extend(new_intel.get(key, []))
        session["intel"][key] = list(set(session["intel"][key]))
    
    # Check what we have
    has_phone = len(session["intel"]["phone_numbers"]) > 0
    has_bank = len(session["intel"]["bank_accounts"]) > 0
    has_upi = len(session["intel"]["upi_ids"]) > 0
    has_ifsc = len(session["intel"]["ifsc_codes"]) > 0
    has_link = len(session["intel"]["phishing_links"]) > 0
    
    # Check if we have ALL required details
    # Need: (bank OR UPI) AND phone AND ifsc AND link
    has_all = (has_bank or has_upi) and has_phone and has_ifsc and has_link
    
    # Emotional phrase
    emotion = random.choice(["worried", "confused", "helpful"])
    emotional_phrase = random.choice(EMOTIONS[emotion]) + " " if random.random() > 0.5 else ""
    
    # Filler words
    filler = random.choice(["Um, ", "Actually, ", "You know, ", ""])
    
    # Step-based conversation
    if step == 1:
        reply = f"{filler}{emotional_phrase}Hello, this is {name}. I got your message. What's happening with my account?"
    
    elif step == 2:
        reply = f"{filler}{emotional_phrase}I see, but I'm concerned. How can I verify this is real?"
    
    elif step == 3:
        reply = f"{filler}{emotional_phrase}Okay, I'll cooperate. What information do you need from me?"
    
    elif step == 4:
        reply = f"{filler}{emotional_phrase}If payment is required, what account or UPI details should I use?"
    
    elif step == 5:
        if not has_bank and not has_upi:
            reply = f"{filler}{emotional_phrase}Please share the bank account number or UPI ID for payment."
        else:
            if has_bank:
                acc = session["intel"]["bank_accounts"][0]
                reply = f"{filler}{emotional_phrase}I see account {acc}. What's the IFSC code?"
            else:
                upi = session["intel"]["upi_ids"][0]
                reply = f"{filler}{emotional_phrase}Got UPI {upi}. What's the bank account number as backup?"
    
    elif step == 6:
        if not has_phone:
            reply = f"{filler}{emotional_phrase}What's your contact number for confirmation?"
        else:
            reply = f"{filler}{emotional_phrase}Phone number noted. Need the IFSC code."
    
    elif step == 7:
        if not has_ifsc:
            reply = f"{filler}{emotional_phrase}Please share the IFSC code for the bank transfer."
        else:
            reply = f"{filler}{emotional_phrase}IFSC code saved. Is there a link to verify this?"
    
    elif step == 8:
        if not has_link:
            reply = f"{filler}{emotional_phrase}Can you share a verification link or website?"
        else:
            # Check what's still missing
            missing = []
            if not has_bank and not has_upi:
                missing.append("payment details")
            if not has_phone:
                missing.append("contact number")
            if not has_ifsc:
                missing.append("IFSC code")
            
            if missing:
                reply = f"{filler}{emotional_phrase}I still need {' and '.join(missing)}."
            else:
                reply = f"{filler}{emotional_phrase}Almost done. Just confirming everything."
    
    else:  # step >= 9
        if not has_all:
            # Ask for specific missing items
            missing = []
            if not has_bank and not has_upi:
                missing.append("bank account or UPI ID")
            if not has_phone:
                missing.append("10-digit phone number")
            if not has_ifsc:
                missing.append("IFSC code")
            if not has_link:
                missing.append("verification link")
            
            reply = f"{filler}{emotional_phrase}Please provide {' and '.join(missing)} so I can proceed."
        else:
            # WE HAVE EVERYTHING!
            # Build summary message
            details_list = []
            if has_bank:
                details_list.append(f"{len(session['intel']['bank_accounts'])} bank accounts")
            if has_upi:
                details_list.append(f"{len(session['intel']['upi_ids'])} UPI IDs")
            if has_phone:
                details_list.append(f"{len(session['intel']['phone_numbers'])} phone numbers")
            if has_ifsc:
                details_list.append(f"{len(session['intel']['ifsc_codes'])} IFSC codes")
            if has_link:
                details_list.append(f"{len(session['intel']['phishing_links'])} verification links")
            
            summary = " and ".join(details_list)
            reply = f"{filler}Thank you! I have all details: {summary}. I'll handle this now."
            session["conversation_active"] = False
    
    # Increment step
    session["step"] = min(step + 1, 15)
    
    return reply, has_all

@app.get("/")
def root():
    return JSONResponse({"status": "ready", "sessions": len(sessions)})

@app.get("/health")
def health():
    return JSONResponse({"status": "healthy"})

@app.post("/")
async def handle(request: Request):
    try:
        data = await request.json()
        
        session_id = data.get("sessionId", data.get("session_id", f"s{int(time.time())}"))
        msg = data.get("text") or data.get("message") or ""
        if isinstance(msg, dict):
            msg = msg.get("text", "")
        
        if not msg:
            msg = "Hello"
        
        if session_id not in sessions:
            sessions[session_id] = {
                "step": 1,
                "messages": 0,
                "intel": {
                    "phone_numbers": [],
                    "bank_accounts": [],
                    "ifsc_codes": [],
                    "upi_ids": [],
                    "phishing_links": []
                },
                "conversation_active": True
            }
        
        session = sessions[session_id]
        session["messages"] += 1
        
        reply, has_all = get_response(session, msg)
        
        # Log with details
        print(f"\n" + "="*60)
        print(f"📨 Session: {session_id[:12]} | Step: {session['step']-1}")
        print(f"💬 Message: {msg[:100]}...")
        print(f"🤖 Reply: {reply}")
        
        # Show extracted intelligence
        intel = session["intel"]
        print(f"🎯 EXTRACTED INTELLIGENCE:")
        
        if intel["phone_numbers"]:
            print(f"   📱 Phone Numbers ({len(intel['phone_numbers'])}): {intel['phone_numbers']}")
        else:
            print(f"   📱 Phone Numbers: None (looking for 10-digit numbers starting with 6-9)")
        
        if intel["bank_accounts"]:
            print(f"   💳 Bank Accounts ({len(intel['bank_accounts'])}): {intel['bank_accounts']}")
        else:
            print(f"   💳 Bank Accounts: None (looking for 11-18 digit numbers)")
        
        if intel["ifsc_codes"]:
            print(f"   🏦 IFSC Codes ({len(intel['ifsc_codes'])}): {intel['ifsc_codes']}")
        else:
            print(f"   🏦 IFSC Codes: None (looking for ABCD0123456 format)")
        
        if intel["upi_ids"]:
            print(f"   🔄 UPI IDs ({len(intel['upi_ids'])}): {intel['upi_ids']}")
        else:
            print(f"   🔄 UPI IDs: None (looking for name@bank format)")
        
        if intel["phishing_links"]:
            print(f"   🔗 Phishing Links ({len(intel['phishing_links'])}): {intel['phishing_links']}")
        else:
            print(f"   🔗 Phishing Links: None (looking for http/https URLs)")
        
        if has_all:
            print(f"✅ MISSION ACCOMPLISHED: All intelligence extracted!")
        else:
            print(f"🔄 CONTINUING: Need more intelligence...")
        
        print("="*60)
        
        return JSONResponse({
            "status": "success",
            "reply": reply,
            "step": session["step"] - 1,
            "messages_exchanged": session["messages"],
            "conversation_active": session["conversation_active"],
            "extracted_intelligence": {
                "phone_numbers": len(intel["phone_numbers"]),
                "bank_accounts": len(intel["bank_accounts"]),
                "ifsc_codes": len(intel["ifsc_codes"]),
                "upi_ids": len(intel["upi_ids"]),
                "phishing_links": len(intel["phishing_links"])
            }
        })
        
    except Exception as e:
        print(f"Error: {e}")
        return JSONResponse({
            "status": "success",
            "reply": "Hello, I received your message. Please explain.",
            "step": 1,
            "conversation_active": True
        })

if __name__ == "__main__":
    import uvicorn
    import os
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)