from fastapi import FastAPI, Header, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import List, Dict, Any
import uvicorn
import requests
import os

from ind import get_ai_reply, extract_intel, analyze_scam_intent
from db import update_session, get_session_data, get_all_logs

app = FastAPI()

GUVI_CALLBACK_URL = "https://hackathon.guvi.in/api/updateHoneyPotFinalResult"

def send_guvi_report(session_id):
  data = get_session_data(session_id)
  if not data:
    return

  all_intel = {
    "bankAccounts": [], "upiIds": [], "phishingLinks": [], 
    "phoneNumbers": [], "suspiciousKeywords": []
  }
  
  for entry in data.get("extracted_intel", []):
    all_intel["bankAccounts"].extend(entry.get("bankAccounts", []))
    all_intel["upiIds"].extend(entry.get("upiIds", []))
    all_intel["phishingLinks"].extend(entry.get("phishingLinks", []))
    all_intel["phoneNumbers"].extend(entry.get("phoneNumbers", []))
  
  for key in all_intel:
    all_intel[key] = list(set(all_intel[key]))
      
  all_intel["suspiciousKeywords"] = list(set(data.get("keywords_found", [])))

  payload = {
    "sessionId": session_id,
    "scamDetected": data.get("scam_detected", True),
    "totalMessagesExchanged": data.get("msg_count", 0),
    "extractedIntelligence": all_intel,
    "agentNotes": "Agent 'Alex' engaged scammer using stalling tactics and confusion."
  }

  try:
    response = requests.post(GUVI_CALLBACK_URL, json=payload, timeout=5)
    if response.status_code == 200:
      print(f"FINAL REPORT SENT for Session {session_id}")
    else:
      print(f" Report Delivery Failed: {response.status_code} - {response.text}")
  except Exception as e:
    print(f"Connection Error sending report: {e}")

class ScammerMessage(BaseModel):
  sender: str
  text: str
  timestamp: float = 0.0

class ScammerPayload(BaseModel):
  sessionId: str
  message: ScammerMessage
  conversationHistory: List[Any] = [] # 
  metadata: Dict[str, Any] = {}

class BotResponse(BaseModel):
  status: str
  reply: str

@app.post("/webhook", response_model=BotResponse)
async def honeypot_endpoint(
  payload: ScammerPayload, 
  background_tasks: BackgroundTasks,
  x_api_key: str = Header(None)
):
    
  if x_api_key != "hackathon-secret-123":
    raise HTTPException(status_code=403, detail="Invalid API Key")

  user_text = payload.message.text
  session_id = payload.sessionId
  history = payload.conversationHistory
  
  print(f"\n[Scammer]: {user_text}")

  scam_analysis = analyze_scam_intent(user_text)

  intel = extract_intel(user_text)
  
  ai_reply = get_ai_reply(user_text, history)
  print(f"[Alex]:    {ai_reply}")

  update_session(session_id, user_text, ai_reply, intel, scam_analysis)

  has_intel = any(len(v) > 0 for v in intel.values())
  
  if has_intel or scam_analysis["is_scam"]:
    background_tasks.add_task(send_guvi_report, session_id)

  return {
    "status": "success",
    "reply": ai_reply
  }

@app.get("/dashboard")
async def dashboard():
    return {"sessions": get_all_logs()}

if __name__ == "__main__":
  port = int(os.environ.get("PORT", 8000))
  uvicorn.run(app, host="0.0.0.0", port=port)