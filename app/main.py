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

def extract_all(text):
    """Extract ALL GUVI-required details"""
    details = {
        "bank_accounts": [],
        "upi_ids": [],
        "phone_numbers": [],
        "ifsc_codes": [],
        "emails": [],
        "phishing_links": [],
        "keywords": []
    }
    
    # Bank accounts (10-18 digits)
    banks = re.findall(r'\b\d{10,18}\b', text)
    details["bank_accounts"] = banks
    
    # UPI IDs
    upis = re.findall(r'[\w.\-]+@(okicici|okhdfcbank|oksbi|paytm|phonepe|gpay|axl|ybl|ibl|upi)', text, re.I)
    details["upi_ids"] = upis
    
    # Phone numbers (10 digits)
    phones = re.findall(r'\b[6789]\d{9}\b', text)
    details["phone_numbers"] = phones
    
    # IFSC codes
    ifscs = re.findall(r'[A-Z]{4}0[A-Z0-9]{6}', text)
    details["ifsc_codes"] = ifscs
    
    # Emails
    emails = re.findall(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', text)
    details["emails"] = emails
    
    # Phishing links (any http/https)
    links = re.findall(r'https?://[^\s]+', text)
    details["phishing_links"] = links
    
    # Suspicious keywords
    keywords = ['urgent', 'verify', 'immediate', 'blocked', 'payment', 'transfer', 'secure', 'login', 'password', 'otp']
    for word in keywords:
        if word in text.lower():
            details["keywords"].append(word)
    
    # Remove duplicates
    for key in details:
        details[key] = list(set(details[key]))
    
    return details

@app.get("/")
def root():
    return {"status": "ready", "sessions": len(sessions)}

@app.get("/health")
def health():
    return {"status": "healthy"}

@app.post("/")
async def handle(request: Request):
    try:
        # Fast parse
        data = await request.json()
        
        # Get session ID
        session_id = data.get("sessionId", data.get("session_id", f"s{int(time.time())}"))
        
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
                "details": {
                    "bank_accounts": [],
                    "upi_ids": [],
                    "phone_numbers": [],
                    "ifsc_codes": [],
                    "emails": [],
                    "phishing_links": [],
                    "keywords": []
                },
                "conversation_active": True
            }
        
        sess = sessions[session_id]
        sess["messages"] += 1
        step = sess["step"]
        
        # Extract details from current message
        new_details = extract_all(msg)
        for key in sess["details"]:
            sess["details"][key].extend(new_details.get(key, []))
            sess["details"][key] = list(set(sess["details"][key]))
        
        # Check what we have
        has_bank = len(sess["details"]["bank_accounts"]) > 0
        has_upi = len(sess["details"]["upi_ids"]) > 0
        has_phone = len(sess["details"]["phone_numbers"]) > 0
        has_ifsc = len(sess["details"]["ifsc_codes"]) > 0
        has_email = len(sess["details"]["emails"]) > 0
        has_link = len(sess["details"]["phishing_links"]) > 0
        
        # Names for realism
        names = ["Raj", "Priya", "Anil", "Meera"]
        name = random.choice(names)
        
        # NEVER END CONVERSATION UNLESS WE HAVE ALL DETAILS
        # Required: (bank OR UPI) AND phone AND ifsc AND email AND link
        has_all_required = (has_bank or has_upi) and has_phone and has_ifsc and has_email and has_link
        
        if has_all_required:
            # WE HAVE EVERYTHING! End conversation
            reply = f"Thank you. I have all details: account, phone, IFSC, email, and link. Will proceed."
            sess["conversation_active"] = False
        else:
            # CONTINUE CONVERSATION - ask for missing details
            if step == 1:
                reply = f"Hello, this is {name}. I got your message. What's happening with my account?"
            elif step == 2:
                reply = "I see. But how do I verify this is genuine? Reference number?"
            elif step == 3:
                reply = "Okay, I want to resolve this. What do you need from me?"
            elif step == 4:
                reply = "If payment required, what account or UPI details?"
            elif step == 5:
                if not has_bank and not has_upi:
                    reply = "Please share account number or UPI ID for payment."
                else:
                    if has_bank:
                        acc = sess["details"]["bank_accounts"][0]
                        reply = f"Got account {acc}. Need IFSC code."
                    else:
                        reply = f"Got UPI. Need bank account as backup?"
            elif step == 6:
                if not has_phone:
                    reply = "What's contact number for confirmation?"
                else:
                    reply = "Need IFSC code for bank transfer."
            elif step == 7:
                if not has_ifsc:
                    reply = "Please share IFSC code for the account."
                else:
                    reply = "What's email for receipt?"
            elif step == 8:
                if not has_email:
                    reply = "Need email address for confirmation."
                else:
                    reply = "Share link to verify or make payment."
            elif step == 9:
                if not has_link:
                    reply = "Please provide website link for verification."
                else:
                    # Still missing something
                    missing = []
                    if not has_bank and not has_upi:
                        missing.append("payment details")
                    if not has_phone:
                        missing.append("phone number")
                    if not has_ifsc:
                        missing.append("IFSC code")
                    if not has_email:
                        missing.append("email")
                    if not has_link:
                        missing.append("verification link")
                    
                    reply = f"Still need {' and '.join(missing)} to proceed."
            else:
                # Keep asking for missing
                missing = []
                if not has_bank and not has_upi:
                    missing.append("account/UPI")
                if not has_phone:
                    missing.append("phone")
                if not has_ifsc:
                    missing.append("IFSC")
                if not has_email:
                    missing.append("email")
                if not has_link:
                    missing.append("link")
                
                if missing:
                    reply = f"Please provide {' and '.join(missing)}."
                else:
                    reply = "Almost done. Need any other details?"
            
            # Increment step for next message
            sess["step"] = min(step + 1, 20)
        
        # Log everything
        print(f"\n" + "="*60)
        print(f"📨 Session: {session_id[:12]} | Step: {step} | Msg: {sess['messages']}")
        print(f"💬 Scammer: {msg[:80]}...")
        print(f"🤖 Reply: {reply}")
        
        # Show extracted details
        print(f"🎯 EXTRACTED DETAILS:")
        details = sess["details"]
        for key, values in details.items():
            if values:
                print(f"   • {key}: {values}")
        
        if not any(len(v) > 0 for v in details.values()):
            print(f"   ⚠️ No details extracted yet")
        
        if has_all_required:
            print(f"✅ SUCCESS: ALL GUVI details extracted!")
        else:
            print(f"🔄 CONTINUING: Need more details...")
        
        print("="*60)
        
        # Return response
        return JSONResponse({
            "status": "success",
            "reply": reply,
            "step": step,
            "messages_exchanged": sess["messages"],
            "conversation_active": sess["conversation_active"],
            "extracted_summary": {
                "bank_accounts": len(details["bank_accounts"]),
                "upi_ids": len(details["upi_ids"]),
                "phone_numbers": len(details["phone_numbers"]),
                "ifsc_codes": len(details["ifsc_codes"]),
                "emails": len(details["emails"]),
                "phishing_links": len(details["phishing_links"]),
                "keywords": len(details["keywords"])
            }
        })
        
    except Exception as e:
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