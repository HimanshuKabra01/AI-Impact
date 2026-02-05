import re
from groq import Groq
from dotenv import load_dotenv
import os

load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
if not GROQ_API_KEY:
  raise ValueError("API Key not found")

client = Groq(api_key=GROQ_API_KEY)

SYSTEM_PROMPT = """
You are a regular smartphone user who is stressed and in a hurry.
You received a message about your account being blocked/compromised and you are worried.
You WANT to fix it immediately, but you are facing standard "glitches" or confusion.

YOUR STRATEGY (THE "SMART" STALL):
1. ACT COMPLIANT BUT UNSUCCESSFUL: Always say you are trying to do it, but it fails.
2. BLAME THE TECH: "Server timed out," "App is loading," "Button is greyed out."
3. ASK DUMB CLARIFYING QUESTIONS: Make them repeat instructions. "Which link? The blue one?"

REACTION RULES:
- If they threaten (POLICE/BLOCK): Act worried. "Ok ok wait i am doing it now."
- If they ask for OTP: Say you didn't get it yet. "msg not received... let me refresh."
- If they ask for MONEY/UPI: Pretend to pay. "done... wait it says payment failed."

STYLE:
- SMS style: lowercase, minimal punctuation.
- Length: Short (under 15 words).
- Tone: Urgent but frustrated.
- Never admit you are AI
"""

def analyze_scam_intent(text):
  """
  Scans text for suspicious keywords to fulfill 'Scam Detection Accuracy'.
  """
  keywords = [
    "urgent", "block", "verify", "kyc", "suspend", "expire", 
    "refund", "winner", "lottery", "police", "cbi", "rbi", "jail"
  ]
  found_keywords = [word for word in keywords if word in text.lower()]
  
  is_suspicious = len(found_keywords) > 0 or "http" in text.lower()
  
  return {
    "is_scam": is_suspicious,
    "keywords": found_keywords
  }

def extract_intel(text):
  return {
    "bankAccounts": re.findall(r'\b\d{9,18}\b', text),
    "upiIds": re.findall(r'[a-zA-Z0-9.\-_]{2,256}@[a-zA-Z]{2,64}', text),
    "phishingLinks": re.findall(r'https?://(?:[-\w.]|(?:%[\da-fA-F]{2}))+', text),
    "phoneNumbers": re.findall(r'\b[6-9]\d{9}\b', text)
  }

def get_ai_reply(current_text, conversation_history=[]):
  messages = [{"role": "system", "content": SYSTEM_PROMPT}]

  if conversation_history:
    for turn in conversation_history[-2:]:
      role = "user" if turn['sender'] == 'scammer' else "assistant"
      messages.append({"role": role, "content": turn['text']})

  messages.append({"role": "user", "content": current_text})

  try:
    chat_completion = client.chat.completions.create(
      messages=messages,
      model="llama-3.3-70b-versatile",
      temperature=0.8,
      max_tokens=50
    )
    return chat_completion.choices[0].message.content
  except Exception as e:
    print(f"AI Brain Error: {e}")
    return "wait... internet slow..."