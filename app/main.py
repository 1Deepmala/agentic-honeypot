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

# Emotional phrases database
EMOTIONS = {
    "worried": [
        "I'm really worried about this...",
        "This is making me anxious...",
        "My heart is racing...",
        "I'm so concerned...",
        "This is really stressful...",
        "I'm panicking a bit...",
        "This has me really nervous..."
    ],
    "confused": [
        "I don't fully understand...",
        "Can you explain that again?",
        "I'm a bit confused...",
        "Let me make sure I get this...",
        "Sorry, I need clarification...",
        "I want to be sure I'm following..."
    ],
    "helpful": [
        "I want to help resolve this...",
        "Let me cooperate to fix this...",
        "I'll do whatever is needed...",
        "I'm ready to help...",
        "Tell me what to do...",
        "I want to get this sorted..."
    ],
    "relieved": [
        "Okay, that makes sense...",
        "I understand now...",
        "That clarifies things...",
        "Good, I'm getting it...",
        "Alright, that helps..."
    ]
}

# Human names and traits
PERSONAS = [
    {"name": "Raj", "age": 32, "job": "accountant", "trait": "cautious"},
    {"name": "Priya", "age": 28, "job": "teacher", "trait": "careful"},
    {"name": "Anil", "age": 45, "job": "shopkeeper", "trait": "trusting"},
    {"name": "Meera", "age": 35, "job": "nurse", "trait": "skeptical"}
]

def extract_details(text):
    """Fast extraction of ALL details"""
    details = {
        "bank_accounts": [],
        "upi_ids": [],
        "phone_numbers": [],
        "ifsc_codes": [],
        "emails": [],
        "phishing_links": []
    }
    
    # Bank accounts (10-18 digits)
    banks = re.findall(r'\b\d{10,18}\b', text)
    details["bank_accounts"] = banks[:3]  # Max 3
    
    # UPI IDs
    upis = re.findall(r'[\w.\-]+@(okicici|okhdfcbank|oksbi|paytm|phonepe|gpay|axl|ybl)', text, re.I)
    details["upi_ids"] = upis[:3]
    
    # Phone numbers (10 digits, starts with 6-9)
    phones = re.findall(r'\b[6789]\d{9}\b', text)
    details["phone_numbers"] = phones[:3]
    
    # IFSC codes
    ifscs = re.findall(r'[A-Z]{4}0[A-Z0-9]{6}', text)
    details["ifsc_codes"] = ifscs[:2]
    
    # Emails
    emails = re.findall(r'[a-z0-9._%+-]+@[a-z0-9.-]+\.[a-z]{2,}', text, re.I)
    details["emails"] = emails[:2]
    
    # Phishing links
    links = re.findall(r'https?://[^\s]+', text)
    details["phishing_links"] = links[:2]
    
    # Remove duplicates
    for key in details:
        details[key] = list(set(details[key]))
    
    return details

def get_human_response(session, msg):
    """Human-like emotional responses"""
    step = session["step"]
    persona = session["persona"]
    name = persona["name"]
    
    # Extract from current message
    new = extract_details(msg)
    for key in session["details"]:
        session["details"][key].extend(new.get(key, []))
        session["details"][key] = list(set(session["details"][key]))
    
    # Check what we have
    has_bank = len(session["details"]["bank_accounts"]) > 0
    has_upi = len(session["details"]["upi_ids"]) > 0
    has_phone = len(session["details"]["phone_numbers"]) > 0
    has_ifsc = len(session["details"]["ifsc_codes"]) > 0
    has_email = len(session["details"]["emails"]) > 0
    has_link = len(session["details"]["phishing_links"]) > 0
    
    # Check if we have ALL required details
    # Need: (bank OR UPI) AND phone AND ifsc AND email AND link
    has_all = (has_bank or has_upi) and has_phone and has_ifsc and has_email and has_link
    
    # Emotional state
    emotion = "worried" if step < 5 else "confused" if step < 10 else "helpful"
    
    # Add emotional phrase (50% chance)
    emotional_phrase = ""
    if random.random() > 0.5:
        emotional_phrase = random.choice(EMOTIONS[emotion]) + " "
    
    # Human filler words
    fillers = ["Um, ", "Actually, ", "You know, ", "I think ", "So, "]
    filler = random.choice(fillers) if random.random() > 0.6 else ""
    
    # Step-based conversation
    if step == 1:
        replies = [
            f"{filler}{emotional_phrase}Hello, this is {name}. I just got your message about my account and I'm really concerned. What's happening exactly?",
            f"{filler}{emotional_phrase}I'm {name}. I received this urgent message and I'm quite worried. Can you explain what's going on with my account?",
            f"{filler}{emotional_phrase}This is {name}. Your message has me really anxious. Which organization is this from and what's the issue?"
        ]
    
    elif step == 2:
        replies = [
            f"{filler}{emotional_phrase}I see, but this is making me nervous. How can I be sure this is legitimate? Do you have any reference number or ID?",
            f"{filler}{emotional_phrase}Okay, but I'm really cautious about these things. Which specific department should I contact to verify this?",
            f"{filler}{emotional_phrase}I want to be careful here. What's your official ID or ticket number so I can confirm this is real?"
        ]
    
    elif step == 3:
        replies = [
            f"{filler}{emotional_phrase}Alright, I'm willing to help resolve this because I'm worried about my account. What exactly do you need from me?",
            f"{filler}{emotional_phrase}I'm anxious but I'll cooperate. What information should I prepare to fix this quickly?",
            f"{filler}{emotional_phrase}Tell me the proper steps. I want to do this correctly but I'm really concerned."
        ]
    
    elif step == 4:
        replies = [
            f"{filler}{emotional_phrase}My friend said to always verify payment details first. If payment is needed, what account or UPI should I use?",
            f"{filler}{emotional_phrase}I'm nervous about payments. Which payment method is safest and what details do I need?",
            f"{filler}{emotional_phrase}For payment, I want to be extra careful. Can you share the account number or UPI ID I should use?"
        ]
    
    elif step == 5:
        if not has_bank and not has_upi:
            replies = [
                f"{filler}{emotional_phrase}I'm still not clear on the payment details. Could you please share the account number or UPI ID?",
                f"{filler}{emotional_phrase}For the payment, I need the exact account number or UPI handle. Can you provide that?",
                f"{filler}{emotional_phrase}To proceed, I require the payment details. What's the account number or UPI ID?"
            ]
        else:
            if has_bank:
                acc = session["details"]["bank_accounts"][0]
                replies = [
                    f"{filler}{emotional_phrase}I see account {acc}. For verification, I need the IFSC code. What is it?",
                    f"{filler}{emotional_phrase}Got account {acc}. Which bank is this and what's the IFSC code?",
                    f"{filler}{emotional_phrase}Regarding account {acc}, I need the IFSC code for the transfer."
                ]
            else:
                replies = [
                    f"{filler}{emotional_phrase}I have the UPI. For backup, can you share the bank account details too?",
                    f"{filler}{emotional_phrase}Got the UPI ID. What's the associated bank account number?",
                    f"{filler}{emotional_phrase}UPI noted. Could you also provide the bank account details?"
                ]
    
    elif step == 6:
        if not has_phone:
            replies = [
                f"{filler}{emotional_phrase}I'm worried about confirmation. What's a contact number I can use for updates?",
                f"{filler}{emotional_phrase}For security, I need a phone number to confirm transactions. What's your number?",
                f"{filler}{emotional_phrase}Can you share a contact number in case I have questions? I want to be sure."
            ]
        else:
            replies = [
                f"{filler}{emotional_phrase}I have the contact number. Now I need the IFSC code for the bank transfer.",
                f"{filler}{emotional_phrase}Phone number noted. What's the IFSC code for the account?",
                f"{filler}{emotional_phrase}Got the number. Please share the IFSC code."
            ]
    
    elif step == 7:
        if not has_ifsc:
            replies = [
                f"{filler}{emotional_phrase}I'm concerned about entering the wrong IFSC. Can you please confirm the IFSC code?",
                f"{filler}{emotional_phrase}For the bank transfer, I need the exact IFSC code. What is it?",
                f"{filler}{emotional_phrase}To avoid errors, please share the IFSC code carefully."
            ]
        else:
            replies = [
                f"{filler}{emotional_phrase}IFSC noted. What email should I use for the receipt?",
                f"{filler}{emotional_phrase}Got the IFSC. Can you provide an email address for confirmation?",
                f"{filler}{emotional_phrase}IFSC code saved. What's the email for documentation?"
            ]
    
    elif step == 8:
        if not has_email:
            replies = [
                f"{filler}{emotional_phrase}I need an email for records. What email address should I use?",
                f"{filler}{emotional_phrase}For the receipt, please share your email address.",
                f"{filler}{emotional_phrase}Can you provide an email for confirmation?"
            ]
        else:
            replies = [
                f"{filler}{emotional_phrase}Email noted. Is there a website or link I should visit for verification?",
                f"{filler}{emotional_phrase}Got the email. Please share any link for more details.",
                f"{filler}{emotional_phrase}Email saved. What link should I check for updates?"
            ]
    
    elif step == 9:
        if not has_link:
            replies = [
                f"{filler}{emotional_phrase}I want to verify everything properly. Can you share a link to the official page?",
                f"{filler}{emotional_phrase}For my peace of mind, please provide a verification link.",
                f"{filler}{emotional_phrase}Is there a website link where I can check the status?"
            ]
        else:
            # Check what's still missing
            missing = []
            if not has_bank and not has_upi:
                missing.append("payment details")
            if not has_phone:
                missing.append("contact number")
            if not has_ifsc:
                missing.append("IFSC code")
            if not has_email:
                missing.append("email")
            
            if missing:
                replies = [
                    f"{filler}{emotional_phrase}I'm still missing {' and '.join(missing)}. Can you provide those?",
                    f"{filler}{emotional_phrase}To complete this, I need {' and '.join(missing)}.",
                    f"{filler}{emotional_phrase}Please share {' and '.join(missing)} so I can proceed."
                ]
            else:
                replies = [
                    f"{filler}{emotional_phrase}Almost done. Just double-checking all details.",
                    f"{filler}{emotional_phrase}Let me confirm everything is correct.",
                    f"{filler}{emotional_phrase}Making sure I have all information."
                ]
    
    else:  # step >= 10
        if not has_all:
            # Ask for specific missing items
            missing = []
            if not has_bank and not has_upi:
                missing.append("account/UPI")
            if not has_phone:
                missing.append("phone number")
            if not has_ifsc:
                missing.append("IFSC")
            if not has_email:
                missing.append("email")
            if not has_link:
                missing.append("verification link")
            
            replies = [
                f"{filler}{emotional_phrase}I'm still concerned I'm missing something. Please provide {' and '.join(missing)}.",
                f"{filler}{emotional_phrase}To feel secure about this, I need {' and '.join(missing)}.",
                f"{filler}{emotional_phrase}Can you share {' and '.join(missing)}? I want to be thorough."
            ]
        else:
            # WE HAVE EVERYTHING!
            replies = [
                f"{filler}Thank you so much! I have all the details now - account, phone, IFSC, email, and verification link. I'll proceed with this immediately.",
                f"{filler}Phew! I've noted down everything correctly. Account details, contact, IFSC, email, and the link. I'll take care of this now.",
                f"{filler}Perfect! I have complete information. Thank you for your patience with all my questions. I'll handle this right away."
            ]
            session["conversation_active"] = False
    
    # Pick random reply
    reply = random.choice(replies)
    
    # Sometimes add hesitation
    if random.random() > 0.7:
        hesitations = ["...", " Let me think... ", " Hmm... ", " You know... "]
        reply = reply + random.choice(hesitations)
    
    # Increment step
    session["step"] = min(step + 1, 20)
    
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
        # Fast parse
        data = await request.json()
        
        # Get session ID
        session_id = data.get("sessionId", data.get("session_id", f"human_{int(time.time())}"))
        
        # Get message
        msg = data.get("text") or data.get("message") or ""
        if isinstance(msg, dict):
            msg = msg.get("text", "")
        
        if not msg:
            msg = "Hello"
        
        # Initialize session
        if session_id not in sessions:
            persona = random.choice(PERSONAS)
            sessions[session_id] = {
                "step": 1,
                "messages": 0,
                "persona": persona,
                "details": {
                    "bank_accounts": [],
                    "upi_ids": [],
                    "phone_numbers": [],
                    "ifsc_codes": [],
                    "emails": [],
                    "phishing_links": []
                },
                "conversation_active": True,
                "start_time": time.time()
            }
        
        session = sessions[session_id]
        session["messages"] += 1
        
        # Get human-like response
        reply, has_all = get_human_response(session, msg)
        
        # Log conversation
        print(f"\n" + "="*50)
        print(f"👤 {session['persona']['name']} ({session['persona']['job']})")
        print(f"📊 Step: {session['step']-1} | Msg: {session['messages']}")
        print(f"💬 Scammer: {msg[:80]}...")
        print(f"🤖 Reply: {reply}")
        
        # Show extracted details
        details = session["details"]
        print(f"🎯 EXTRACTED:")
        for key, values in details.items():
            if values:
                print(f"   • {key}: {values}")
        
        if not any(len(v) > 0 for v in details.values()):
            print(f"   ⚠️ No details yet")
        
        if has_all:
            print(f"✅ SUCCESS: ALL details extracted! Conversation complete.")
        else:
            print(f"🔄 CONTINUING: Still extracting...")
        
        print("="*50)
        
        return JSONResponse({
            "status": "success",
            "reply": reply,
            "step": session["step"] - 1,
            "messages_exchanged": session["messages"],
            "conversation_active": session["conversation_active"],
            "extracted": {
                "bank_accounts": len(details["bank_accounts"]),
                "upi_ids": len(details["upi_ids"]),
                "phone_numbers": len(details["phone_numbers"]),
                "ifsc_codes": len(details["ifsc_codes"]),
                "emails": len(details["emails"]),
                "phishing_links": len(details["phishing_links"])
            }
        })
        
    except Exception as e:
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