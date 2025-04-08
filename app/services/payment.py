import httpx,requests
from app.utils.http_responses import Responses
import logging
logging.basicConfig(level=logging.INFO)

headers = {
            "x-api-version": "2025-01-01",
            "x-client-id": "TEST10529007816a91c0f1d078a4506770092501",
            "x-client-secret": "cfsk_ma_test_883c650b5d4fb6de59ddfef6b10fbf91_49be6136",
            "Content-Type": "application/json"
        }

class PaymentService:
    @staticmethod
    async def create_order(user_id, amount, phone_number):
        print(type(amount), "Type of amount:::::::::::::::::::::")
        
        url = "https://sandbox.cashfree.com/pg/orders"
        payload = {
            "order_currency": "INR",
            "order_amount": amount,
            "customer_details": {
                "customer_id": user_id,
                "customer_phone": phone_number
            }
        }
        async with httpx.AsyncClient() as client:
            response = await client.post(url, json=payload, headers=headers)
        return response.json()
    
    
    @staticmethod
    async def get_order_status(order_id:str):
        try:
            url = "https://sandbox.cashfree.com/pg/orders/{order_id}".format(order_id=order_id)
            # print("----------",url)
            response = requests.request("GET", url, headers=headers)
            if response.status_code == 200:
                return response.json()
            return None
        except Exception as e:
            logging.error("Error in OrderId: %s", str(e))
            return Responses.error(500, str(e))
        
