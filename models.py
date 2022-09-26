from pydantic import BaseModel

class BaseResponse(BaseModel):
    error: str | None
    success: bool| None

class GeneralChecksResponse(BaseResponse):
    pass

class LateCheckinsCheckResponse(BaseResponse):
    pass
