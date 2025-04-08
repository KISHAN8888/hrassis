from starlette.responses import RedirectResponse
from app.validators.user_validator import SignUpValidator as sign_up_validator, SignInValidator as sign_in_validator
from app.utils.http_responses import Responses
from app.helpers.auth_helper import AuthHelper as auth_helper
from app.repository.user_repository import UserRepository as user_db
from app.services.user_services import Auth as auth
from app.services.user_services import OAuth as oauth
from app.config.env_config import env_config
from fastapi import Request,Depends
from app.middlewares.auth_middleware import AuthMiddleware as auth_middleware
from app.services.payment import PaymentService as payment_service
from app.helpers.generate_pass import generate_otp,hash_otp
from app.helpers.gen_email_temp import forgot_password_template
from app.repository.order_repository import OrderRepository as OrderDbServices
from app.middlewares.auth_middleware import AuthMiddleware as Auth
from app.models.user_model import ExternalService
from typing import Optional, Any
from urllib.parse import unquote
import json

from app.utils.email import send_email


import logging,uuid,datetime,jwt,os

logging.basicConfig(level=logging.INFO)

class UserControllers:
    @staticmethod
    async def sign_up(body: sign_up_validator):
        "Sign up a new user"
        try:
            user = await user_db.get_user_by_email(body.email)

            if user:
                return Responses.error(400, message="User already exists... please proceed to login")
            hashed_password = await auth_helper.hash_password(body.password)
            user = await user_db.insert_user(email=body.email,name=body.name, company_name=body.company_name, password=hashed_password)
            if not user:
                return Responses.error(400, message="Error creating user")
            token = await auth.create_jwt_token(user)
            if not token:
                return Responses.error(400, message="Something went wrong, Unable to generate Access Token")
            return Responses.success(200, message="User created successfully", data={"token":token})
        except Exception as e:
            logging.error("Error creating user: %s", str(e))
            return Responses.error(500, message=str(e))

    @staticmethod
    async def sign_in(body: sign_in_validator):
        "Sign in a user"
        try:
            user = await user_db.get_user_by_email(body.email)
            if not user:
                return Responses.error(400, message="User not found... please sign up")
            db_password = await user_db.get_user_by_email_with_password(body.email)
            if not db_password:
                return Responses.error(400, message="Something went wrong, Try again later")
            
            verify_password = await auth_helper.verify_password(body.password, db_password["password"])
            if not verify_password:
                return Responses.error(400, message="Invalid email or password")
            
            token = await auth.create_jwt_token(user)
            if not token:
                return Responses.error(400, message="Something went wrong, Unable to generate Access Token")
            return Responses.success(200, message="User loggedIn successfully", data={"token":token})
        except Exception as e:
            return Responses.error(500, str(e))
    
    @staticmethod
    async def google_login(code:str, state:Optional[Any] = None):
        "Login with google only"
        try:    
            tokens = await oauth.exchange_code_for_tokens(code)
            access_token, id_token = tokens["access_token"], tokens["id_token"]
            user_info = await oauth.fetch_user_info(access_token, id_token)

            email, name = user_info.get("email"), user_info.get("name")

            if not email:
                return Responses.error(400, message="Error fetching email, please try again later")
            
            if state:
                decoded_state = unquote(state) 
                state_data = json.loads(decoded_state) 
                
                if state_data["email"] != email:
                    return Responses.error(400, message="Email not matched with login email")
            
            user = await user_db.get_user_by_email(email)

            if not user:
                user = await user_db.insert_user(
                    email=email,
                    name=name,
                    oauth_refresh_token=tokens.get("refresh_token"),
                    enabled_services=[ExternalService.GOOGLE_AUTH]
                )

            elif state!=None and state_data["service"]=="google_auth" and ExternalService.GOOGLE_AUTH not in user.get("enabled_services", []):
                result = await user_db.update_users_services(user["user_id"], [ExternalService.GOOGLE_AUTH], tokens.get("refresh_token"))

                if not result:
                    return Responses.error(400, message="Error updating user services")
                
                return RedirectResponse(url=f"{env_config.oauth.fe_redirect_url}")
            
            elif state!=None and state_data["service"]=="gmail" and ExternalService.GMAIL not in user.get("enabled_services", []):
                result = await user_db.update_users_services(user["user_id"], [ExternalService.GMAIL], tokens.get("refresh_token"))

                if not result:
                    return Responses.error(400, message="Error updating user services")
                
                return RedirectResponse(url=f"{env_config.oauth.fe_redirect_url}")
            
            token = await auth.create_jwt_token(user)

            if not token:
                logging.error("Error creating token")
                return Responses.error(400, message="Something went wrong, unable to generate access token")
            
            return RedirectResponse(url=f"{env_config.oauth.fe_redirect_url}?token={token}")
        except Exception as e:
            logging.error("Error during Google login: %s", str(e))
            return Responses.error(500, str(e))
        
    @staticmethod
    async def payment_cashFree(request: Request, user = Depends(auth_middleware.authenticate_user)):
        try:
            print(user,"User::::")
            data = await request.json()
            amount = data.get("amount")
            phone_number = data.get("phone_number")
            payment_source = data.get("payment_source")
            # orderId = str(uuid.uuid4())
            print("Data::",data)
            amount_to_credits = {1: 1,49: 40,100: 100,149: 200}
            credits = amount_to_credits.get(amount)
            print(type(credits),"Type of Credits:")
            if credits is None:
                return Responses.error(400,"Invalid amount")
            response = await payment_service.create_order(user['user_id'], int(amount), phone_number)
            if not response:
                return Responses.error(400,"Payment service is down or Inputs are not in valid Syntax")
            order_id = response['order_id']
            create_order = await user_db.create_order(user['user_id'],credits,amount,order_id,payment_source)
            return Responses.success(200, message="Order created successfully", data={"Response": response,"order_id":create_order})
        except Exception as e:
            logging.error("Error in OrderId: %s", str(e))
            return Responses.error(500, str(e))    
        
        
    @staticmethod
    async def payment_status_by_order_id(order_id:str,payment_source:str,user=Depends(auth_middleware.authenticate_user)):
        try:
            response = await payment_service.get_order_status(order_id)
            if not response:
                return Responses.error(400,"Payment service is down or Inputs are not in valid Syntax")
            if response['order_status'] == "FAILED":
                await user_db.update_status(order_id,'failed')
                
            if response["order_status"] == 'PAID':
                await user_db.update_status(order_id,'success')
                if payment_source == "service":
                    # increase the credits in the service_model
                    pass
                else:
                    is_status_update = await user_db.update_credits(order_id,user['user_id'])
                    if not is_status_update:
                        return Responses.error(400,"Error in updating credits")                 
            return Responses.success(200, message="Success", data={"Response": response})
        except Exception as e:
            logging.error("Error in OrderId: %s", str(e))
            
            
    @staticmethod
    async def send_otp(request:Request):
        try:
            data = await request.json()
            print("data", data)
            email = data.get("email")
            print("Varun")
            user = await user_db.get_user_by_email(email)
            if not user:
                return Responses.error(400, message="User not found... please sign up")
            otp = generate_otp()
            otp_hash = hash_otp(otp=otp,email=email)
            token_payload = {
            "otp_hash": otp_hash,
            "email": email,
            "exp": datetime.datetime.utcnow() + datetime.timedelta(minutes=10)
            }
            token = jwt.encode(token_payload, env_config.auth.secret_key, algorithm=env_config.auth.algorithm)
            emailTemplate = forgot_password_template(otp=otp)
            print(otp,"otp:::::::::::::::::::::")
            email_sent = send_email(email,emailTemplate,"Reset Your Password")
            if not email_sent:
                return Responses.error(400, message="Error in sending email")
            return Responses.success(200, message="Otp sent successfully", data={"token": token})
        except Exception as e:
            logging.error("Error in Send Otp: %s", str(e))
            return Responses.error(500, message=str(e))            
            
    @staticmethod
    async def verify_otp(request:Request):
        try:
            data = await request.json()
            otp = data.get("otp")
            token = data.get("token")
            if not token or not otp:
                return Responses.error(400, message="Token or OTP not provided")
            decoded_payload = jwt.decode(token, env_config.auth.secret_key, algorithms=[env_config.auth.algorithm])
            email = decoded_payload.get('email')
            otp_hash = decoded_payload.get('otp_hash')
            print(otp) 
            genrate_otp_hash = hash_otp(otp,email)
            if otp_hash != genrate_otp_hash:
                return Responses.error(400, message="Invalid OTP")
            user = await user_db.get_user_by_email(email)
            token = await auth.create_jwt_token(user)
            return Responses.success(200, message="Otp verified successfully", data={"token": token})            
        except Exception as e:
            logging.error("Error in Verify Otp: %s", str(e))
            return Responses.error(500, message=str(e))
        
        
    @staticmethod    
    async def reset_password(request:Request,user=Depends(auth_middleware.authenticate_user)):
        try:
            data = await request.json()
            password = data.get("password")
            if not password:
                return Responses.error(400, message="Password not provided")
            user = await user_db.get_user_by_email(user["email"])
            if not user:
                return Responses.error(400, message="User not found... please sign up")
            print("1234",str(password))
            hashed_password = await auth_helper.hash_password(password)
            hashed_password_str = hashed_password.decode()
            print("----------",hashed_password_str)
            reset_password = await user_db.update_password(user["user_id"],hashed_password_str)
            if not reset_password:
                return Responses.error(400, message="Error in updating password")
            return Responses.success(200, message="Password updated successfully")
        except Exception as e: 
            logging.error("Error in Reset Password: %s", str(e))
            return Responses.error(500, message=str(e))
        
    @staticmethod
    async def get_order_of_user(user=Depends(Auth.authenticate_user)):
        try:
            order = await OrderDbServices.get_order_by_id(user["user_id"])
            if not order:
                return Responses.error(404,f"Order not found with your UserId: {user['user_id']}")
            return Responses.success(200, f"Successfully fetched Orders for User_Id: {user['user_id']}", order)
        except Exception as e:
            logging.warning("Orders not found: %s", str(e))
            return Responses.error(404, "Orders not found")
        

    @staticmethod
    async def users_enabled_services(user = Depends(Auth.authenticate_user)):
        try:
            user = await user_db.get_user_by_email(user["email"])

            if not user :
                return Responses.error(401, message="Unauthorized")
            
            enabled_services = user.get("enabled_services")

            return Responses.success(200, message="Success", data={"enabled_services": enabled_services})
        except Exception as e:
            logging.error("Error in Enable User Google Service: %s", str(e))
            return Responses.error(500, message=str(e))
        