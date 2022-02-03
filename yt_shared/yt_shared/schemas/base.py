import orjson
from pydantic import BaseModel, Extra


def orjson_dumps(v, *, default) -> str:
    return orjson.dumps(v, default=default).decode()


class RealBaseModel(BaseModel):
    class Config:
        extra = Extra.forbid
        json_loads = orjson.loads
        json_dumps = orjson_dumps
