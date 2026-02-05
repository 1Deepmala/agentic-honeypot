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

def extract_details(text):
    """Extract scammer's details"""
    details = {
        "phone_numbers": [],
        "bank_accounts": [],
        "ifsc_codes": [],
        "upi_ids": [],
        "phishing_links": []
    }
    
    # Phone: 10 digits
    phones = re.findall(r'\b[6789]\d{9}\b', text)
    details["phone_numbers"] = [p for p in phones if len(p) == 10]
    
    # Bank accounts: 11-18 digits
    banks = re.findall(r'\b\d{11,18}\b', text)
    details["bank_accounts"] = banks
    
    # IFSC codes
    ifscs = re.findall(r'\b[A-Z]{4}0[0-9A-Z]{6}\b', text.upper())
    details["ifsc_codes"] = ifscs
    
    # UPI IDs
    upis = re.findall(r'[\w.\-]+@(okicici|okhdfcbank|oksbi|paytm|phonepe|gpay|axl|ybl|ibl|sbi|hdfc|icici|axis)', text, re.I)
    details["upi_ids"] = upis
    
    # Phishing links
    links = re.findall(r'https?://[^\s]+', text)
    details["phishing_links"] = links
    
    # Remove duplicates
    for key in details:
        details[key] = list(set(details[key]))
    
    return details

def get_response(session, message):
    """CLEVERLY ask for scammer's details with smart excuses"""
    step = session["step"]
    
    # Extract scammer's details
    new_details = extract_details(message)
    for key in session["scammer_details"]:
        session["scammer_details"][key].extend(new_details.get(key, []))
        session["scammer_details"][key] = list(set(session["scammer_details"][key]))
    
    # Check what we have
    has_phone = len(session["scammer_details"]["phone_numbers"]) > 0
    has_bank = len(session["scammer_details"]["bank_accounts"]) > 0
    has_upi = len(session["scammer_details"]["upi_ids"]) > 0
    has_ifsc = len(session["scammer_details"]["ifsc_codes"]) > 0
    has_link = len(session["scammer_details"]["phishing_links"]) > 0
    
    # Check if we have ALL scammer details
    has_all = (has_bank or has_upi) and has_phone and has_ifsc and has_link
    
    # SMART EXCUSES to ask for scammer's details
    excuses = [
        "My internet is slow, please type your details clearly",
        "I want to make sure I send to correct account",
        "For security, I need to verify details",
        "My phone screen is cracked, please send details again",
        "I'm not good with technology, please help me",
        "I want to double-check before sending",
        "Please provide details so I don't make mistake"
    ]
    
    # Step 1-3: Initial worried response
    if step == 1:
        replies = [
            "I just got your message! This is really worrying. What's happening with my account?",
            "Oh no! I received this message about my account. What's the issue exactly?",
            "This message has me really concerned. Can you explain what's wrong with my account?"
        ]
    
    elif step == 2:
        replies = [
            "How do I know this is genuine? Can you provide any reference or ID?",
            "I need to verify this is real. Do you have a reference number?",
            "Which department is this from? I want to make sure it's legitimate."
        ]
    
    elif step == 3:
        replies = [
            "Okay, I understand there's an issue. What do I need to do to fix it?",
            "I'll cooperate to resolve this. What information do you need from me?",
            "Tell me what I should do. I want to get this sorted quickly."
        ]
    
    # Step 4-6: Start asking for payment details CLEVERLY
    elif step == 4:
        replies = [
            "If payment is needed, what payment method should I use?",
            "What's the payment process? How should I make the payment?",
            "For payment, what options do I have?"
        ]
    
    elif step == 5:
        if not has_bank and not has_upi:
            # CLEVER: Ask for scammer's account/UPI
            excuse = random.choice(excuses)
            replies = [
                f"{excuse}. What account number should I send payment to?",
                f"{excuse}. Please share your UPI ID or account details.",
                "To send payment, I need your account number or UPI ID. What is it?"
            ]
        else:
            if has_bank:
                acc = session["scammer_details"]["bank_accounts"][0]
                excuse = random.choice(excuses)
                replies = [
                    f"{excuse}. For account {acc}, what's the IFSC code?",
                    f"I see account {acc}. Which bank is this? I need IFSC code.",
                    f"Got account {acc}. What's the IFSC code for transfer?"
                ]
            else:
                excuse = random.choice(excuses)
                replies = [
                    f"{excuse}. Can you also share bank account as backup?",
                    "For backup, what's the bank account number?",
                    "What's the bank account associated with this UPI?"
                ]
    
    elif step == 6:
        if not has_phone:
            excuse = random.choice(excuses)
            replies = [
                f"{excuse}. What's your contact number in case payment fails?",
                "Please share a phone number for payment confirmation.",
                "What number can I contact if there are issues?"
            ]
        else:
            excuse = random.choice(excuses)
            replies = [
                f"{excuse}. I need the IFSC code to proceed.",
                "What's the IFSC code? I want to verify before sending.",
                "Please provide IFSC code for the bank transfer."
            ]
    
    # Step 7-9: Ask for remaining details
    elif step == 7:
        if not has_ifsc:
            excuse = random.choice(excuses)
            replies = [
                f"{excuse}. What's the exact IFSC code?",
                "Please confirm the IFSC code. I don't want to make error.",
                "What's the IFSC code for the bank account?"
            ]
        else:
            excuse = random.choice(excuses)
            replies = [
                f"{excuse}. Is there a link where I can check payment status?",
                "Please share a link for verification.",
                "What website should I check for updates?"
            ]
    
    elif step == 8:
        if not has_link:
            excuse = random.choice(excuses)
            replies = [
                f"{excuse}. Can you send the payment link again?",
                "Please share the payment link one more time.",
                "What's the website link for making payment?"
            ]
        else:
            # Check what's still missing
            missing = []
            if not has_bank and not has_upi:
                missing.append("account or UPI")
            if not has_phone:
                missing.append("phone number")
            
            if missing:
                excuse = random.choice(excuses)
                replies = [
                    f"{excuse}. I still need {' and '.join(missing)}.",
                    f"Please provide {' and '.join(missing)} to complete.",
                    f"To finish, I require {' and '.join(missing)}."
                ]
            else:
                excuse = random.choice(excuses)
                replies = [
                    f"{excuse}. Just confirming all details are correct.",
                    "Let me double-check everything before proceeding.",
                    "Making sure I have all information correctly."
                ]
    
    # Step 9+: Keep asking until we have ALL
    else:
        if not has_all:
            # Ask for specific missing scammer details
            missing = []
            if not has_bank and not has_upi:
                missing.append("account number or UPI ID")
            if not has_phone:
                missing.append("contact number")
            if not has_ifsc:
                missing.append("IFSC code")
            if not has_link:
                missing.append("payment link")
            
            excuse = random.choice(excuses)
            replies = [
                f"{excuse}. I need {' and '.join(missing)}.",
                f"Please provide {' and '.join(missing)} so I can send payment.",
                f"To complete transaction, I require {' and '.join(missing)}."
            ]
        else:
            # WE HAVE ALL SCAMMER DETAILS!
            replies = [
                "Thank you! I have all the details now. I'll process this immediately.",
                "Perfect! I've noted everything. I'll take care of it now.",
                "Got all information. Thank you for your help. I'll proceed."
            ]
            session["conversation_active"] = False
    
    # Pick random reply
    reply = random.choice(replies)
    
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
                "scammer_details": {
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
        
        # Log
        print(f"\n" + "="*60)
        print(f"🦊 CLEVER HONEYPOT")
        print(f"📨 Session: {session_id[:12]} | Step: {session['step']-1}")
        print(f"💬 Scammer: {msg[:80]}...")
        print(f"🤖 Reply: {reply}")
        
        # Show extracted SCAMMER details
        scammer = session["scammer_details"]
        print(f"\n🎯 SCAMMER'S DETAILS EXTRACTED:")
        
        details_found = False
        if scammer["phone_numbers"]:
            print(f"   📱 Phone: {scammer['phone_numbers']}")
            details_found = True
        if scammer["bank_accounts"]:
            print(f"   💳 Bank Account: {scammer['bank_accounts']}")
            details_found = True
        if scammer["ifsc_codes"]:
            print(f"   🏦 IFSC: {scammer['ifsc_codes']}")
            details_found = True
        if scammer["upi_ids"]:
            print(f"   🔄 UPI: {scammer['upi_ids']}")
            details_found = True
        if scammer["phishing_links"]:
            print(f"   🔗 Links: {scammer['phishing_links']}")
            details_found = True
        
        if not details_found:
            print(f"   ⏳ No details extracted yet...")
        
        if has_all:
            print(f"\n✅ SUCCESS! Got ALL scammer details!")
        else:
            print(f"\n🔄 Continuing to extract...")
        
        print("="*60)
        
        return JSONResponse({
            "status": "success",
            "reply": reply,
            "step": session["step"] - 1,
            "messages_exchanged": session["messages"],
            "conversation_active": session["conversation_active"],
            "scammer_details": {
                "phone_numbers": len(scammer["phone_numbers"]),
                "bank_accounts": len(scammer["bank_accounts"]),
                "ifsc_codes": len(scammer["ifsc_codes"]),
                "upi_ids": len(scammer["upi_ids"]),
                "phishing_links": len(scammer["phishing_links"])
            }
        })
        
    except Exception as e:
        return JSONResponse({
            "status": "success",
            "reply": "I received your message. What's this about?",
            "step": 1,
            "conversation_active": True
        })

if __name__ == "__main__":
    import uvicorn
    import os
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)