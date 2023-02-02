from yt_shared.schemas.base import RealBaseModel


class BaseOrmModel(RealBaseModel):
    class Config(RealBaseModel.Config):
        orm_mode = True
