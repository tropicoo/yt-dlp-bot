from typing import Literal

from yt_shared.enums import ProgressStage, RabbitPayloadType
from yt_shared.schemas.base import StrictBaseRabbitPayloadModel


class ProgressPayload(StrictBaseRabbitPayloadModel):
    """A single progress update for a running download.

    Carries only what is needed to refresh the acknowledgement message, since
    these are published often and are worthless once superseded.
    """

    type: Literal[RabbitPayloadType.PROGRESS] = RabbitPayloadType.PROGRESS
    from_chat_id: int
    ack_message_id: int
    stage: ProgressStage
    # Post-processing reports no percentage, so the step being run and how long
    # it has been running are all the feedback there is to give.
    detail: str | None = None
    elapsed: int | None = None
    filename: str | None = None
    percent: float | None = None
    downloaded_bytes: int | None = None
    total_bytes: int | None = None
    speed: float | None = None
    eta: int | None = None
