import random

def generate_fake_profile():
  first_names = ["Rajesh", "Suresh", "Amit", "Anita", "Sunita", "Ramesh"]
  last_names = ["Kumar", "Sharma", "Verma", "Gupta", "Singh", "Patel"]
  banks = ["SBI", "HDFC", "ICICI", "PNB"]
  
  profile = {
    "name": f"{random.choice(first_names)} {random.choice(last_names)}",
    "bank_name": random.choice(banks),
    "account_number": str(random.randint(30000000000, 39999999999)),
    "ifsc": f"{random.choice(banks).upper()}{random.randint(10000, 99999)}",
    "balance": f"₹{random.randint(45000, 150000)}",
    "fake_otp": str(random.randint(1000, 9999)),
    "upi_pin": str(random.randint(1000, 9999))
  }
  return profile