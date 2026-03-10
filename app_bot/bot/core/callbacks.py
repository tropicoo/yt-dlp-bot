import logging
from itertools import product
from urllib.parse import urljoin, urlparse

from pyrogram.enums import ParseMode
from pyrogram.types import CallbackQuery, Message
from yt_shared.constants import REMOVE_QUERY_PARAMS_HOSTS
from yt_shared.emoji import SUCCESS_EMOJI
from yt_shared.enums import DownMediaType, TaskSource, TelegramChatType, VideoQuality
from yt_shared.rabbit.publisher import RmqPublisher
from yt_shared.schemas.media import InbMediaPayload

from bot.bot.client import VideoBotClient
from bot.core.keyboards import (
    CANCEL_PREFIX,
    DOWNLOAD_PREFIX,
    MEDIA_TYPE_PREFIX,
    build_media_type_keyboard,
    build_quality_keyboard,
)
from bot.core.pending_downloads import PendingDownload, PendingDownloadsStore
from bot.core.schemas import UserSchema
from bot.core.utils import bold, can_remove_url_params, get_user_id


class TelegramCallback:
    _MSG_CHOOSE_FORMAT: str = '🎯 Choose download format:'
    _MSG_CHOOSE_QUALITY: str = '📊 Choose video quality:'
    _MSG_SEND_OK: str = (
        f'{SUCCESS_EMOJI} {bold("{count}URL{plural} sent for download")}'
    )
    _MSG_SEND_FAIL: str = f'🛑 {bold("Failed to send URL for download")}'
    _MSG_CANCELLED: str = '❌ Download cancelled'

    def __init__(self) -> None:
        self._log = logging.getLogger(self.__class__.__name__)
        self._rmq_publisher = RmqPublisher()

    @staticmethod
    async def on_start(client: VideoBotClient, message: Message) -> None:  # noqa: ARG004
        await message.reply(
            bold('Send video URL to start processing'),
            parse_mode=ParseMode.HTML,
            reply_to_message_id=message.id,
        )

    async def on_message(self, client: VideoBotClient, message: Message) -> None:
        """Receive video URL and show format selection keyboard."""
        self._log.debug('Received Telegram Message: %s', message)
        text = message.text
        if not text:
            self._log.debug('Forwarded message, skipping')
            return

        urls = text.splitlines()
        user = client.allowed_users[get_user_id(message)]
        if user.use_url_regex_match:
            urls = self._filter_urls(
                urls=urls, regexes=client.conf.telegram.url_validation_regexes
            )
            if not urls:
                self._log.debug('No urls to download, skipping message')
                return

        # Process each URL - show format selection keyboard
        for url in urls:
            await self._show_format_selection(message=message, url=url, user=user)

    async def _show_format_selection(
        self, message: Message, url: str, user: UserSchema
    ) -> None:
        """Show inline keyboard for format selection."""
        from_user_id = message.from_user.id if message.from_user else None

        # Preprocess URL
        if can_remove_url_params(url=url, matching_hosts=REMOVE_QUERY_PARAMS_HOSTS):
            processed_url = urljoin(url, urlparse(url).path)
        else:
            processed_url = url

        # Send message with format selection keyboard
        ack_message = await message.reply(
            text=f'{self._MSG_CHOOSE_FORMAT}\n\n<code>{url}</code>',
            parse_mode=ParseMode.HTML,
            reply_to_message_id=message.id,
            reply_markup=build_media_type_keyboard(
                url_id=PendingDownloadsStore.generate_url_id(
                    message.chat.id, message.id
                )
            ),
        )

        # Store pending download
        url_id = PendingDownloadsStore.generate_url_id(message.chat.id, message.id)
        pending = PendingDownload(
            url=processed_url,
            original_url=url,
            from_chat_id=message.chat.id,
            from_chat_type=TelegramChatType(message.chat.type.value),
            from_user_id=from_user_id,
            message_id=message.id,
            ack_message_id=ack_message.id,
            save_to_storage=user.save_to_storage,
            user=user,
        )
        PendingDownloadsStore.add(url_id, pending)

    async def on_callback_query(
        self, client: VideoBotClient, callback_query: CallbackQuery
    ) -> None:
        """Handle callback queries from inline keyboards."""
        data = callback_query.data
        self._log.debug('Received callback query: %s', data)

        if data.startswith(MEDIA_TYPE_PREFIX):
            await self._handle_media_type_selection(callback_query)
        elif data.startswith(DOWNLOAD_PREFIX):
            await self._handle_download_selection(callback_query)
        elif data.startswith(CANCEL_PREFIX):
            await self._handle_cancel(callback_query)

    async def _handle_media_type_selection(
        self, callback_query: CallbackQuery
    ) -> None:
        """Handle media type selection (Video/Audio/Both)."""
        data = callback_query.data.removeprefix(MEDIA_TYPE_PREFIX)
        parts = data.split(':')

        if len(parts) != 2:
            await callback_query.answer('Invalid selection')
            return

        media_type_str, url_id = parts

        # Handle back button
        if media_type_str == 'back':
            pending = PendingDownloadsStore.get(url_id)
            if not pending:
                await callback_query.answer('Session expired')
                await callback_query.message.delete()
                return

            await callback_query.message.edit_text(
                text=f'{self._MSG_CHOOSE_FORMAT}\n\n<code>{pending.original_url}</code>',
                parse_mode=ParseMode.HTML,
                reply_markup=build_media_type_keyboard(url_id),
            )
            await callback_query.answer()
            return

        pending = PendingDownloadsStore.get(url_id)
        if not pending:
            await callback_query.answer('Session expired. Please send the URL again.')
            await callback_query.message.delete()
            return

        try:
            media_type = DownMediaType(media_type_str)
        except ValueError:
            await callback_query.answer('Invalid media type')
            return

        # For audio, directly start download
        if media_type == DownMediaType.AUDIO:
            await self._start_download(
                callback_query=callback_query,
                url_id=url_id,
                media_type=media_type,
                quality=VideoQuality.BEST,
            )
            return

        # For video, show quality selection
        await callback_query.message.edit_text(
            text=f'{self._MSG_CHOOSE_QUALITY}\n\n<code>{pending.original_url}</code>',
            parse_mode=ParseMode.HTML,
            reply_markup=build_quality_keyboard(url_id, media_type),
        )
        await callback_query.answer()

    async def _handle_download_selection(
        self, callback_query: CallbackQuery
    ) -> None:
        """Handle download with selected quality."""
        data = callback_query.data.removeprefix(DOWNLOAD_PREFIX)
        parts = data.split(':')

        if len(parts) != 3:
            await callback_query.answer('Invalid selection')
            return

        media_type_str, quality_str, url_id = parts

        try:
            media_type = DownMediaType(media_type_str)
            quality = VideoQuality(quality_str)
        except ValueError:
            await callback_query.answer('Invalid selection')
            return

        await self._start_download(
            callback_query=callback_query,
            url_id=url_id,
            media_type=media_type,
            quality=quality,
        )

    async def _start_download(
        self,
        callback_query: CallbackQuery,
        url_id: str,
        media_type: DownMediaType,
        quality: VideoQuality,
    ) -> None:
        """Start the download process."""
        pending = PendingDownloadsStore.remove(url_id)
        if not pending:
            await callback_query.answer('Session expired. Please send the URL again.')
            await callback_query.message.delete()
            return

        # Build quality text for message
        quality_text = ''
        if media_type != DownMediaType.AUDIO:
            quality_map = {
                VideoQuality.BEST: 'Best',
                VideoQuality.UHD_4K: '4K',
                VideoQuality.QHD_1440P: '1440p',
                VideoQuality.FHD_1080P: '1080p',
                VideoQuality.HD_720P: '720p',
                VideoQuality.SD_480P: '480p',
                VideoQuality.LD_360P: '360p',
            }
            quality_text = f' ({quality_map.get(quality, quality)})'

        media_type_emoji = {
            DownMediaType.VIDEO: '🎬',
            DownMediaType.AUDIO: '🎵',
            DownMediaType.AUDIO_VIDEO: '🎬+🎵',
        }

        # Update message to show download started
        await callback_query.message.edit_text(
            text=(
                f'{SUCCESS_EMOJI} {bold("Download started")}\n\n'
                f'{media_type_emoji.get(media_type, "")} '
                f'{media_type.value}{quality_text}\n'
                f'<code>{pending.original_url}</code>'
            ),
            parse_mode=ParseMode.HTML,
        )
        await callback_query.answer('Download started!')

        # Send to worker
        payload = InbMediaPayload(
            url=pending.url,
            original_url=pending.original_url,
            message_id=pending.message_id,
            ack_message_id=pending.ack_message_id,
            from_user_id=pending.from_user_id,
            from_chat_id=pending.from_chat_id,
            from_chat_type=pending.from_chat_type,
            source=TaskSource.BOT,
            save_to_storage=pending.save_to_storage,
            download_media_type=media_type,
            video_quality=quality,
            custom_filename=None,
            automatic_extension=False,
        )

        is_sent = await self._rmq_publisher.send_for_download(payload)
        if not is_sent:
            self._log.error('Failed to publish URL %s to message broker', pending.url)
            await callback_query.message.edit_text(
                text=self._MSG_SEND_FAIL,
                parse_mode=ParseMode.HTML,
            )

    async def _handle_cancel(self, callback_query: CallbackQuery) -> None:
        """Handle cancel button."""
        url_id = callback_query.data.removeprefix(CANCEL_PREFIX)
        PendingDownloadsStore.remove(url_id)

        await callback_query.message.edit_text(
            text=self._MSG_CANCELLED,
            parse_mode=ParseMode.HTML,
        )
        await callback_query.answer('Cancelled')

    def _filter_urls(self, urls: list[str], regexes: list[str]) -> list[str]:
        """Return valid urls."""
        import re

        self._log.debug('Matching urls: %s against regexes %s', urls, regexes)
        valid_urls: list[str] = []
        for url, regex in product(urls, regexes):
            if re.match(regex, url):
                valid_urls.append(url)

        valid_urls = list(dict.fromkeys(valid_urls))
        self._log.debug('Matched urls: %s', valid_urls)
        return valid_urls
