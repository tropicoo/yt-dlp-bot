import asyncio
import html
from typing import Any, ClassVar

from pyrogram.enums import ParseMode
from yt_shared.enums import RabbitPayloadType
from yt_shared.schemas.error import ErrorDownloadGeneralPayload, ErrorDownloadPayload

from bot.core.config import settings
from bot.core.error_messages import (
    FriendlyError,
    classify,
    extract_reason,
    strip_extractor_prefix,
)
from bot.core.handlers.abstract import AbstractDownloadHandler
from bot.core.i18n import t
from bot.core.utils import split_telegram_message
from bot.version import __version__


class ErrorDownloadHandler(AbstractDownloadHandler):
    _body: ErrorDownloadPayload | ErrorDownloadGeneralPayload
    _DETAILS_PLACEHOLDER = '{details}'

    _ERR_MSG_HEADER_KEY_MAP: ClassVar[dict[RabbitPayloadType, str]] = {
        RabbitPayloadType.DOWNLOAD_ERROR: 'error.header_download',
        RabbitPayloadType.GENERAL_ERROR: 'error.header_general',
    }

    async def handle(self) -> None:
        await self._send_error_text()

    async def _send_error_text(self) -> None:
        recipients = self._get_receiving_users()

        # The status message is the natural place for the outcome, so a failure
        # takes it over the same way a success removes it.
        sender_language = self._bot.language_for(
            self._get_sender_id(), self._body.from_chat_id
        )
        if await self._replace_status_message(
            self._format_error_message(sender_language)
        ):
            recipients = [u for u in recipients if u.id != self._body.from_chat_id]

        # Rendered per recipient: the same failure reaches people who may not
        # share a language.
        for user in recipients:
            kwargs: dict[str, Any] = {
                'chat_id': user.id,
                'text': self._format_error_message(self._bot.language_for(user.id)),
                'parse_mode': ParseMode.HTML,
            }
            if self._body.message_id:
                kwargs['reply_to_message_id'] = self._body.message_id
            asyncio.create_task(self._bot.send_message(**kwargs))  # noqa:RUF006

    async def _replace_status_message(self, text: str) -> bool:
        """Turn the "Download started" message into the error report."""
        chat_id = self._body.from_chat_id
        message_id = self._body.context.ack_message_id
        if not (chat_id and message_id):
            return False

        try:
            await self._bot.edit_message_text(
                chat_id=chat_id,
                message_id=message_id,
                text=text,
                parse_mode=ParseMode.HTML,
            )
        except Exception as err:
            # Falling back to a separate message is better than losing the report.
            self._log.warning(
                'Could not replace the status message %s, sending a new one: %s',
                message_id,
                err,
            )
            return False
        return True

    def _format_error_message(self, language: str) -> str:
        """Explain expected failures, report everything else in full detail."""
        friendly_error = classify(self._body.exception_msg)
        if friendly_error is not None:
            self._log.info(
                'Reporting expected download failure "%s" for %s',
                friendly_error.name,
                self._body.url,
            )
            return self._format_friendly_message(friendly_error, language)
        return self._format_detailed_message(language)

    def _format_friendly_message(
        self, friendly_error: FriendlyError, language: str
    ) -> str:
        reason = strip_extractor_prefix(self._body.exception_msg)
        return '\n'.join((
            f'{friendly_error.emoji} <b>{t(friendly_error.title_key, language)}</b>',
            '',
            t(friendly_error.hint_key, language),
            '',
            f'🔗 <b>{t("error.label_url", language)}:</b> '
            f'<code>{html.escape(self._body.url)}</code>',
            f'💬 <b>{t("error.label_site_response", language)}:</b> '
            f'<code>{html.escape(reason)}</code>',
            f'🏷️ <b>{t("error.label_tag", language)}:</b> '
            f'{t("error.tag_unavailable", language)}',
        ))

    def _format_detailed_message(self, language: str) -> str:
        """Report an unrecognised failure, leading with whatever reason we have.

        The raw text is only repeated under "Details" when it says more than the
        reason line, which spares the reader a duplicated one-liner.
        """
        raw_msg = (self._body.exception_msg or '').strip()
        stripped_msg = strip_extractor_prefix(raw_msg)
        reason = extract_reason(raw_msg)
        has_details = bool(stripped_msg) and stripped_msg != reason

        lines = [
            f'🛑 <b>{t(self._ERR_MSG_HEADER_KEY_MAP[self._body.type], language)}</b>',
            '',
            f'💬 <b>{t("error.label_reason", language)}:</b> '
            f'{html.escape(reason or self._body.message)}',
            f'📹 <b>{t("error.label_url", language)}:</b> '
            f'<code>{self._body.url}</code>',
            f'ℹ <b>{t("error.label_task_id", language)}:</b> '  # noqa: RUF001
            f'<code>{self._body.task_id}</code>',
            f'🌊 <b>{t("error.label_source", language)}:</b> '
            f'<code>{self._body.context.source.value}</code>',
        ]
        if has_details:
            lines.append(
                f'👀 <b>{t("error.label_details", language)}:</b> '
                f'<code>{self._DETAILS_PLACEHOLDER}</code>'
            )
        lines.extend((
            f'⬇️ <b>{t("error.label_ytdlp_version", language)}:</b> '
            f'<code>{self._body.yt_dlp_version}</code>',
            f'🤖 <b>{t("error.label_bot_version", language)}:</b> '
            f'<code>{__version__}</code>',
            f'🏷️ <b>{t("error.label_tag", language)}:</b> '
            f'{t("error.tag_error", language)}',
        ))
        pre_formatted_message = '\n'.join(lines)
        if not has_details:
            return pre_formatted_message

        exception_msg = html.escape(raw_msg)
        msg_len = len(pre_formatted_message) - len(self._DETAILS_PLACEHOLDER)
        exc_msg_len = len(exception_msg)
        self._log.debug('Length of exception_msg %s', exc_msg_len)
        self._log.debug('Length of pre_formatted_message %s', msg_len)
        if msg_len + exc_msg_len > settings.TG_MAX_MSG_SIZE:
            exception_msg = next(
                split_telegram_message(
                    text=exception_msg,
                    chunk_size=settings.TG_MAX_MSG_SIZE - msg_len,
                    return_first=True,
                    negate=True,
                )
            )
        # Substituted rather than formatted: the reason comes from yt-dlp and
        # may itself contain braces, which would break another format pass.
        message = pre_formatted_message.replace(
            self._DETAILS_PLACEHOLDER, exception_msg
        )
        self._log.debug('Length of formatted_message %s', len(message))
        return message
