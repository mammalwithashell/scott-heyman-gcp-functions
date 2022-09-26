from pydantic import BaseModel

class BaseResponse(BaseModel):
    error: str | None
    success: bool| None
    message: str | None

class GeneralChecksResponse(BaseResponse):
    pass

class LateCheckinsCheckResponse(BaseResponse):
    pass
