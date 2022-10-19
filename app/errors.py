from fastapi import HTTPException


class ErrorCode:
    def internal_server_error(self, message: str):
        raise HTTPException(status_code=500, detail=message)

    def bad_request_error(self, message: str):
        raise HTTPException(status_code=400, detail=message)
