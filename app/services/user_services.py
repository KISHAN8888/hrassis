from typing import Dict
import logging
from datetime import datetime, timedelta, timezone
from jose import JWTError, jwt
import httpx
from app.config.env_config import env_config
from app.helpers.auth_helper import AuthHelper as auth_helper
from app.utils.http_responses import Responses

logging.basicConfig(level=logging.INFO)

class Auth:
    @staticmethod
    async def create_jwt_token(data: dict) -> str:
        "create a login token for the user."
        try:
            hashed_uid = await auth_helper.hash_password(data["user_id"])
            to_encode = {
                "user_id": data["user_id"], 
                "email": data["email"], 
                "name": data["name"], 
                "hash": str(hashed_uid),
                "role":data["role"],
                "exp": int((datetime.now(timezone.utc) + timedelta(hours=int(env_config.auth.access_expiration_hours))).timestamp())
            }
            encoded_jwt = jwt.encode(to_encode, env_config.auth.secret_key, env_config.auth.algorithm)
            return encoded_jwt
        except JWTError as e:
            logging.error("Error ocurred while creating JWT token: %s", e)
            return Responses.error(401, message="Invalid authentication credentials")
        
    @staticmethod
    async def decode_token(token: str) -> Dict:
        "Checks token's validity"
        try:
            payload = jwt.decode(token, env_config.auth.secret_key, algorithms=[env_config.auth.algorithm])
            return payload
        except JWTError as e:
            logging.error("Error ocurred while decoding JWT token: %s", e)
            return Responses.error(401, message="Invalid authentication credentials")
        
class OAuth:
    "OAuth services for Google"
    @staticmethod
    async def exchange_code_for_tokens(code: str):
        "Exchange code for tokens from Google"
        try:
            token_url = "https://oauth2.googleapis.com/token"
            payload = {"code": code, "client_id": env_config.oauth.client_id, "client_secret": env_config.oauth.client_secret,
                       "redirect_uri": env_config.oauth.redirect_url, "grant_type": "authorization_code",}
            headers = {"Content-Type": "application/json"}
            response = httpx.post(token_url, json=payload, headers=headers)
            if response.status_code != 200:
                return Responses.error(400, message="Failed to fetch tokens")
            return response.json()
        except Exception as e:
            return Responses.error(500, message=str(e))
        
    @staticmethod
    async def fetch_user_info(access_token: str, id_token: str):
        "Fetch user information from Google"
        try: 
            user_info_url = f"https://www.googleapis.com/oauth2/v1/userinfo?alt=json&access_token={access_token}"
            headers = {"Authorization": f"Bearer {id_token}"}
            
            async with httpx.AsyncClient() as client:
                response = await client.get(user_info_url, headers=headers)

            if response.status_code != 200:
                raise Exception("Failed to fetch user information")
            
            user_info = response.json()
            
            return user_info
        except Exception as e:
            raise Exception(str(e))
        
    @staticmethod
    async def fetch_user_contacts(access_token: str):
        "Fetch user contacts from Google People API (Read-Only)"
        try:
            headers = {"Authorization": f"Bearer {access_token}"}
            params = {"personFields": "names,emailAddresses,phoneNumbers", "pageSize": 500}

            async with httpx.AsyncClient() as client:
                response = await client.get("https://people.googleapis.com/v1/people/me/connections", headers=headers, params=params)

            if response.status_code != 200:
                logging.error("Failed to fetch user contacts: %s", response.text)
                return []

            contacts_data = response.json().get("connections", [])
            return [
                {
                    "name": contact.get("names", [{}])[0].get("displayName", "Unknown"),
                    "email": contact.get("emailAddresses", [{}])[0].get("value", None),
                    "phone": contact.get("phoneNumbers", [{}])[0].get("value", None)
                }
                for contact in contacts_data
            ]
        except Exception as e:
            logging.error("E" \
            "rror fetching user contacts: %s", str(e))
            raise str(e)
        
    @staticmethod
    async def fetch_directory_contacts(access_token: str):
        """Fetch organization directory contacts from Google People API"""
        try:
            headers = {"Authorization": f"Bearer {access_token}"}
            params = {
                "readMask": "names,emailAddresses",
                "sources": "DIRECTORY_SOURCE_TYPE_DOMAIN_PROFILE",
                "pageSize": 500,
                "query": "*"  
            }

            async with httpx.AsyncClient() as client:
                response = await client.get(
                    "https://people.googleapis.com/v1/people:searchDirectoryPeople",
                    headers=headers,
                    params=params
                )

            if response.status_code != 200:
                logging.error("Failed to fetch directory contacts: %s", response.text)
                return []

            directory_data = response.json().get("people", [])
            return [
                {
                    "name": person.get("names", [{}])[0].get("displayName", "Unknown"),
                    "email": person.get("emailAddresses", [{}])[0].get("value", None),
                }
                for person in directory_data
            ]
        except Exception as e:
            logging.error("Error fetching directory contacts: %s", str(e))
            raise str(e)
        
