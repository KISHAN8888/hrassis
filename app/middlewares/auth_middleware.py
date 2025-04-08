from fastapi import Request,HTTPException
from app.services.user_services import Auth as auth_service
from app.utils.http_responses import Responses
from app.repository.user_repository import UserRepository as user_db
from fastapi.responses import JSONResponse as JsonResponse


class AuthMiddleware:
    @staticmethod
    async def authenticate_user(request: Request, allowed_roles=['hr']):
        """Authenticates the user and checks their role if required"""
        try:
            token = request.headers.get("Authorization")
            print("Varun",token)
            if not token or not token.startswith("Bearer "):
                return Responses.error(401, "Unauthorized: Missing or invalid token format")
            
            token = token.split("Bearer ")[1]
            payload = await auth_service.decode_token(token)
            # print(payload,"payload")
            if not payload:
                raise HTTPException(status_code=401, detail="Unauthorized: Missing or invalid token format")

            # Extract user email from token
            user_email = payload.get("email")
            if not user_email:
                raise HTTPException(status_code=401, detail="Unauthorized: Invalid or expired token")

            # Fetch user role from DB
            user = await user_db.get_user_by_email(payload["email"])
            user_role = user['role']
            print(user_role,":::::::::role")
            
            if not user_role:
                raise HTTPException(status_code=403, detail="Forbidden: Role not found")
                # return Responses.error(403, "Forbidden: Role not found")

            # Check if role is allowed
            if user_role == payload.get("role") and user_role in allowed_roles:
                return payload
            else:
                raise HTTPException(status_code=403, detail="Forbidden: Insufficient role")
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")
    