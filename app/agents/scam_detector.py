import re

class ScamDetector:
    def detect(self, message: str):
        message_lower = message.lower()
        
        # Simple scam detection
        scam_keywords = [
            "verify", "account", "locked", "password",
            "click", "link", "http", "urgent", "immediate",
            "upi", "payment", "send money", "bank"
        ]
        
        score = 0
        for keyword in scam_keywords:
            if keyword in message_lower:
                score += 1
        
        is_scam = score >= 3
        confidence = min(score / len(scam_keywords), 1.0)
        
        return {
            "is_scam": is_scam,
            "confidence": round(confidence, 2),
            "score": score
        }