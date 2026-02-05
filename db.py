from pymongo import MongoClient
import os
from datetime import datetime
from dotenv import load_dotenv

MONGO_URI = os.getenv("MONGO_URI")
if not MONGO_URI:
  raise ValueError("URI not found in env") 

client = MongoClient(MONGO_URI)
db = client["honeypot_db"]
sessions = db["sessions"]

def update_session(session_id, user_text, ai_reply, intel, scam_analysis):
  sessions.update_one(
    {"session_id": session_id},
    {
      "$inc": {"msg_count": 2},
      "$push": {
        "history": {
          "$each": [
            {"role": "scammer", "content": user_text},
            {"role": "agent", "content": ai_reply}
          ]
        },
        "extracted_intel": intel,
        "keywords_found": {"$each": scam_analysis["keywords"]}
      },
      "$set": {
        "last_active": datetime.utcnow(),
        "scam_detected": scam_analysis["is_scam"]
      }
    },
    upsert=True
  )

def get_session_data(session_id):
  return sessions.find_one({"session_id": session_id})

def get_all_logs():
  return list(sessions.find({}, {"_id": 0}).sort("last_active", -1))