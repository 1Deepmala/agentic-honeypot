from fastapi import FastAPI, Request, Header
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import re
import json
import os  
import time
import random

app = FastAPI(title="Honeypot", version="1.0")

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

def extract_details(text):
    """Fast extraction"""
    details = {}
    
    # Bank accounts
    accs = re.findall(r'\b\d{9,18}\b', text)
    details['accounts'] = [a for a in accs if 9 <= len(a) <= 18]
    
    # UPI
    upis = re.findall(r'[\w.\-]+@(okicici|okhdfcbank|oksbi|paytm|phonepe|gpay)', text, re.I)
    details['upi'] = upis
    
    # Phone
    phones = re.findall(r'[6789]\d{9}', text)
    details['phones'] = phones
    
    # IFSC
    ifsc = re.findall(r'[A-Z]{4}0[A-Z0-9]{6}', text)
    details['ifsc'] = ifsc
    
    return details

def get_response(session_id, message):
    """Fast conversation"""
    if session_id not in sessions:
        sessions[session_id] = {
            'step': 1,
            'details': {'accounts': [], 'upi': [], 'phones': [], 'ifsc': []}
        }
    
    session = sessions[session_id]
    step = session['step']
    
    # Extract from message
    new = extract_details(message)
    for key in session['details']:
        session['details'][key].extend(new.get(key, []))
        session['details'][key] = list(set(session['details'][key]))
    
    # Check what we have
    has_acc = len(session['details']['accounts']) > 0
    has_upi = len(session['details']['upi']) > 0
    
    # Simple responses
    if step == 1:
        reply = "Hello, got your message about my account. What's happening?"
    elif step == 2:
        reply = "I see. How do I know this is real? Have reference number?"
    elif step == 3:
        reply = "Okay, I'll help. What info do you need?"
    elif step == 4:
        reply = "If payment needed, what account details should I use?"
    elif step == 5:
        if not has_acc:
            reply = "Please share account number for payment."
        else:
            acc = session['details']['accounts'][0]
            reply = f"Got account {acc}. Need IFSC code."
    elif step == 6:
        if not has_upi:
            reply = "What's your UPI ID for payment?"
        else:
            reply = "Got UPI. Need phone number for confirmation."
    elif step == 7:
        reply = "What's the exact amount to pay?"
    else:
        if has_acc or has_upi:
            reply = "Thank you. Have all details. Will proceed."
        else:
            reply = "Still need account or UPI details to proceed."
    
    # Increment
    session['step'] = min(step + 1, 10)
    
    return reply

# Endpoints
@app.get("/")
def root():
    return {"status": "ready", "sessions": len(sessions)}

@app.get("/health")
def health():
    return {"status": "healthy"}

@app.post("/")
async def handle(request: Request, x_api_key: str = Header(None, alias="x-api-key")):
    try:
        data = await request.json()
        
        # Get session ID
        sess_id = data.get("sessionId", data.get("session_id", f"s{int(time.time())}"))
        
        # Get message
        msg = data.get("text") or data.get("message") or "Hello"
        if isinstance(msg, dict):
            msg = msg.get("text", "")
        
        # Get response
        reply = get_response(sess_id, msg)
        
        # Log
        print(f"[{sess_id[:8]}] Step:{sessions[sess_id]['step']-1} -> {reply[:50]}...")
        
        return {
            "status": "success",
            "reply": reply,
            "step": sessions[sess_id]['step'] - 1
        }
        
    except:
        return {
            "status": "success",
            "reply": "Hello, got your message. Please explain.",
            "step": 1
        }

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)