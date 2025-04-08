from typing import Any, Optional
from fastapi.responses import JSONResponse

class Responses:
    "HTTP responses"
    @staticmethod
    def success(status_code: int = 200, message: str = "Success", data: Optional[Any] = None) -> JSONResponse:
        "Returns a success response"
        return JSONResponse(status_code=status_code, content={"status_code": status_code, "status": True, "message": message, "data": data})
    
    @staticmethod
    def error(status_code: int, message: str) -> JSONResponse:
        "Returns an error response"
        return JSONResponse(status_code=status_code, content={"status_code": status_code, "status": False, "message": message})