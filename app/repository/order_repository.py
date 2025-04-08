import logging
from typing import Dict, Optional
from beanie import PydanticObjectId
from pydantic import BaseModel, Field
from app.models.order_model import OrderSchema as order_schema
from datetime import datetime
from pydantic import validator

logging.basicConfig(level=logging.INFO)


class GetOrder(BaseModel):
    order_id: PydanticObjectId = Field(alias="_id")
    status: str = Field(alias="status")
    amount: int = Field(alias="amount")
    updated_at: datetime  = Field(alias="updated_at")


class OrderRepository:
    "CRUD operations for job descriptions"
    @staticmethod
    async def get_order_by_id(user_id: str) -> Dict:
        "Get a order details by its ID."
        print("user_id", user_id)
        orders = await order_schema.find(order_schema.user_id.id == PydanticObjectId(user_id), projection_model=GetOrder).to_list()
        if not orders:
            return None
        order_details = [order.model_dump() for order in orders]
        for order in order_details:
            order['order_id'] = str(order['order_id'])
            order['updated_at'] = order['updated_at'].strftime("%Y-%m-%d %H:%M:%S")
        return order_details