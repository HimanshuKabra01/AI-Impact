from pymongo import MongoClient
from pymongo.errors import ServerSelectionTimeoutError
import os
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

MONGO_URI = os.getenv("MONGO_URI")

try:
    client = MongoClient(
        MONGO_URI, 
        tlsAllowInvalidCertificates=True, 
        serverSelectionTimeoutMS=9000,
        connectTimeoutMS=9000
    )
    db = client["honeypot_db"]
    sessions = db["sessions"]
    client.admin.command('ismaster')
    print("MongoDB Connected Successfully")
except Exception as e:
    print(f"MongoDB Connection Failed: {e}")
    sessions = None

def update_session(session_id, user_text, ai_reply, intel, scam_analysis):
  if sessions is None:
      print("DB not available, skipping save.")
      return

  try:
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
  except Exception as e:
    print(f"DB Write Error: {e}")

def get_session_data(session_id):
  if sessions is None: return {}
  try:
    return sessions.find_one({"session_id": session_id})
  except:
    return {}

def get_all_logs():
  if sessions is None: return []
  try:
    return list(sessions.find({}, {"_id": 0}).sort("last_active", -1))
  except:
    return []