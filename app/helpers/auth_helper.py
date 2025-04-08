import bcrypt


class AuthHelper:
    @staticmethod
    async def hash_password(password: str) -> bytes:
        """Hash a password using bcrypt."""
        salt = bcrypt.gensalt(6) 
        return bcrypt.hashpw(password.encode(), salt) 
    
    @staticmethod
    async def verify_password(password: str, hashed_password: bytes) -> bool:
        """Verify a password against a hashed password using bcrypt."""
        return bcrypt.checkpw(password.encode(), hashed_password.encode())  
