import re
from groq import Groq
from dotenv import load_dotenv
import os
from fake_data import generate_fake_profile  # Make sure Step 1 is done

load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
if not GROQ_API_KEY:
  raise ValueError("API Key not found")

client = Groq(api_key=GROQ_API_KEY)

# --- PERSONA 1: THE VICTIM (For Scammers) ---
SCAM_VICTIM_PROMPT = """
ou are a regular smartphone user who is stressed and in a hurry.
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

NORMAL_USER_PROMPT = """
You are Alex, a normal, relaxed guy. You are chatting with a friend or colleague.
- Be casual, friendly, and brief.
- Use lowercase and standard SMS slang (lol, yeah, k).
- DO NOT mention banks, police, or money unless they do.
- If they act weird, just ask "what do u mean?".
"""

def analyze_scam_intent(text):
  """
  Basic keyword check for the Dashboard (Legacy).
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

def classify_intent_smart(text):
    """
    THE CHAMELEON ROUTER:
    Uses a fast AI call to decide if the message is malicious or safe.
    """
    try:
        completion = client.chat.completions.create(
            messages=[
                {"role": "system", "content": "Classify this message as 'SCAM' (if it contains threats, financial demands, phishing, or generic spam) or 'SAFE' (if it looks like normal chat). Reply ONLY with the word SCAM or SAFE."},
                {"role": "user", "content": text}
            ],
            model="llama-3.3-70b-versatile",
            temperature=0.0,
            max_tokens=5
        )
        result = completion.choices[0].message.content.strip().upper()
        return "SCAM" in result
    except:
        return True

def get_ai_reply(current_text, conversation_history=[]):
  is_scam_likely = classify_intent_smart(current_text)
  
  fake_user = generate_fake_profile()
  
  if is_scam_likely:
      base_prompt = SCAM_VICTIM_PROMPT
      dynamic_details = f"""
      YOUR FAKE IDENTITY (USE THESE CONSISTENTLY):
      - Name: {fake_user['name']}
      - Bank: {fake_user['bank_name']}
      - Account No: {fake_user['account_number']}
      - Balance: {fake_user['balance']} (Act rich but confused)
      """
  else:
      base_prompt = NORMAL_USER_PROMPT
      dynamic_details = "Just act like a normal friend. Ignore the fake banking details."

  final_system_prompt = f"{base_prompt}\n{dynamic_details}"

  messages = [{"role": "system", "content": final_system_prompt}]

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
      max_tokens=150
    )
    return chat_completion.choices[0].message.content
  except Exception as e:
    print(f"AI Brain Error: {e}")
    return "wait... internet slow..."