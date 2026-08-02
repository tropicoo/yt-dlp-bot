"""Turning source chapters into timestamps Telegram can seek with.

Telegram makes a timestamp clickable inside the caption of an audio or video
message, and inside any message replying to one, seeking the media to that
point. A long recording therefore becomes navigable simply by listing its
chapters — no player controls required.
"""

from collections.abc import Iterable, Sequence

from yt_shared.schemas.media import Chapter


def format_timestamp(seconds: float) -> str:
    """Render a position the way Telegram recognises it: ``9:07`` or ``1:09:07``."""
    total = max(0, int(seconds))
    hours, remainder = divmod(total, 3600)
    minutes, secs = divmod(remainder, 60)
    if hours:
        return f'{hours}:{minutes:02d}:{secs:02d}'
    return f'{minutes}:{secs:02d}'


def format_chapters(chapters: Iterable[Chapter]) -> list[str]:
    return [f'{format_timestamp(c.start_time)} {c.title}' for c in chapters]


def group_into_messages(lines: Sequence[str], limit: int) -> list[str]:
    """Group lines into messages of at most ``limit`` characters.

    Splits between lines only: half a chapter is worse than an extra message,
    and a truncated timestamp would stop being a link.
    """
    messages: list[str] = []
    current: list[str] = []
    length = 0

    for line in lines:
        # +1 for the newline that will join this line to the previous one.
        addition = len(line) + (1 if current else 0)
        if current and length + addition > limit:
            messages.append('\n'.join(current))
            current, length = [line], len(line)
            continue
        current.append(line)
        length += addition

    if current:
        messages.append('\n'.join(current))
    return messages
