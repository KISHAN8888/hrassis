import random
import string,bcrypt

def generate_otp():
  """Generate a 4-digit numeric OTP."""
  return ''.join(str(random.randint(0, 9)) for _ in range(4))



FIXED_SALT = bcrypt.gensalt(rounds=12)  # Generate once and reuse
def hash_otp(otp: str,email: str) -> str:
    hash = otp+email
    hashed_otp = bcrypt.hashpw(hash.encode(), FIXED_SALT)
    return hashed_otp.decode()

