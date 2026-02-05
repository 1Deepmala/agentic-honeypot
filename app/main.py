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
        
        # Get session
        session_id = data.get("sessionId", f"s{int(time.time())}")
        
        if session_id not in sessions:
            sessions[session_id] = {
                "step": 1,
                "messages": 0,
                "bank": [],
                "upi": [],
                "phone": [],
                "links": []
            }
        
        sess = sessions[session_id]
        sess["messages"] += 1
        step = sess["step"]
        
        # Get message
        msg = data.get("text") or data.get("message") or "Hello"
        if isinstance(msg, dict):
            msg = msg.get("text", "")
        
        # Simple extraction
        # Bank
        banks = re.findall(r'\b\d{9,18}\b', msg)
        sess["bank"].extend([b for b in banks if 9 <= len(b) <= 18])
        
        # UPI
        upis = re.findall(r'[\w.\-]+@(okicici|okhdfcbank|oksbi|paytm|phonepe|gpay)', msg, re.I)
        sess["upi"].extend(upis)
        
        # Phone
        phones = re.findall(r'[6789]\d{9}', msg)
        sess["phone"].extend(phones)
        
        # Links
        urls = re.findall(r'https?://[^\s]+', msg)
        sess["links"].extend(urls)
        
        # Remove duplicates
        sess["bank"] = list(set(sess["bank"]))
        sess["upi"] = list(set(sess["upi"]))
        sess["phone"] = list(set(sess["phone"]))
        sess["links"] = list(set(sess["links"]))
        
        # Check if we have everything
        has_bank = len(sess["bank"]) > 0
        has_upi = len(sess["upi"]) > 0
        has_phone = len(sess["phone"]) > 0
        has_links = len(sess["links"]) > 0
        
        # Simple conversation
        name = random.choice(["Raj", "Priya", "Anil"])
        
        if step == 1:
            reply = f"Hello, this is {name}. Got your message. What's happening?"
        elif step == 2:
            reply = "I see. How do I know this is real? Reference?"
        elif step == 3:
            reply = "Okay, I'll help. What info needed?"
        elif step == 4:
            reply = "If payment, what account details?"
        elif step == 5:
            if not has_bank and not has_upi:
                reply = "Please share account number or UPI."
            else:
                if has_bank:
                    reply = f"Got account. Need IFSC."
                else:
                    reply = "Got UPI. Need phone for confirmation."
        elif step == 6:
            if not has_phone:
                reply = "What's contact number?"
            else:
                reply = "Need link to verify."
        elif step == 7:
            if not has_links:
                reply = "Share link for verification."
            else:
                reply = "Got link. What's amount?"
        elif step >= 8:
            # Check if we have everything
            if (has_bank or has_upi) and has_phone and has_links:
                # WE HAVE ALL! End conversation
                reply = "Thank you. Have all details. Will proceed."
                # Don't increment step - conversation ends
            else:
                # Keep asking
                missing = []
                if not has_bank and not has_upi:
                    missing.append("payment details")
                if not has_phone:
                    missing.append("contact")
                if not has_links:
                    missing.append("link")
                
                reply = f"Still need {' and '.join(missing)}."
                sess["step"] += 1
        else:
            reply = "Please provide more details."
            sess["step"] += 1
        
        # Only increment step if not in final check phase
        if step < 8:
            sess["step"] += 1
        
        # Log
        print(f"\n[{session_id[:8]}] Step:{step} Msg:{sess['messages']}")
        print(f"Scammer: {msg[:60]}...")
        print(f"Reply: {reply}")
        if has_bank or has_upi or has_phone or has_links:
            print(f"Extracted: Bank:{sess['bank']} UPI:{sess['upi']} Phone:{sess['phone']} Links:{sess['links']}")
        
        return {
            "status": "success",
            "reply": reply,
            "step": step,
            "messages": sess["messages"],
            "extracted": {
                "bank": len(sess["bank"]),
                "upi": len(sess["upi"]),
                "phone": len(sess["phone"]),
                "links": len(sess["links"])
            }
        }
        
    except Exception as e:
        return {
            "status": "success",
            "reply": "Hello, received your message. Please explain.",
            "step": 1
        }

if __name__ == "__main__":
    import uvicorn
    import os
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port, timeout_keep_alive=30)