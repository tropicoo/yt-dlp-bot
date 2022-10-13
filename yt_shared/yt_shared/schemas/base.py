from pydantic import BaseModel, Extra


class RealBaseModel(BaseModel):
    class Config:
        extra = Extra.forbid
