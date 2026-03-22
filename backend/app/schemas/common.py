from pydantic import BaseModel


class MetaSchema(BaseModel):
    request_id: str
    timestamp: str


class SuccessEnvelope(BaseModel):
    success: bool = True
    data: dict[str, object]
    meta: MetaSchema


class ErrorBody(BaseModel):
    code: str
    message: str
    details: dict[str, object] = {}


class ErrorEnvelope(BaseModel):
    success: bool = False
    error: ErrorBody
    meta: MetaSchema