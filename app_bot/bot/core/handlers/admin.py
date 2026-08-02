"""Admin command handlers for bot configuration management."""

import logging
import sys

from pyrogram.enums import ParseMode
from pyrogram.types import Message

from bot.bot.client import VideoBotClient
from bot.core.config.config_manager import config_manager
from bot.core.exceptions import (
    CannotDeleteAdminError,
    UserAlreadyExistsError,
    UserNotFoundError,
)
from bot.core.i18n import t


class AdminCommandHandler:
    """Handles admin commands for bot configuration."""

    def __init__(self) -> None:
        self._log = logging.getLogger(self.__class__.__name__)

    def _is_admin(self, bot: VideoBotClient, user_id: int) -> bool:
        """Check if user is an admin."""
        return user_id in bot.admin_users

    @staticmethod
    def _sender_id(message: Message) -> int:
        return message.from_user.id if message.from_user else message.chat.id

    @staticmethod
    def _tick(value: bool) -> str:
        return '✅' if value else '❌'

    async def _reply(self, message: Message, text: str) -> None:
        """Send reply with HTML formatting."""
        await message.reply(
            text=text,
            parse_mode=ParseMode.HTML,
            reply_to_message_id=message.id,
        )

    async def _reply_t(
        self, client: VideoBotClient, message: Message, key: str, **params
    ) -> None:
        """Reply in the language of the admin who ran the command."""
        language = client.language_for(self._sender_id(message), message.chat.id)
        await self._reply(message, t(key, language, **params))

    async def _refuse_non_admin(self, client: VideoBotClient, message: Message) -> bool:
        """Turn away anyone who is not an admin, and say so in their language."""
        if self._is_admin(client, self._sender_id(message)):
            return False
        await self._reply_t(client, message, 'admin.not_admin')
        return True

    async def on_adduser(self, client: VideoBotClient, message: Message) -> None:
        """Handle /adduser <user_id> command."""
        if await self._refuse_non_admin(client, message):
            return

        parts = message.text.split()
        if len(parts) != 2:
            await self._reply_t(client, message, 'admin.adduser_usage')
            return

        try:
            new_user_id = int(parts[1])
        except ValueError:
            await self._reply_t(client, message, 'admin.invalid_user_id')
            return

        try:
            user = config_manager.add_user(client, new_user_id)
        except UserAlreadyExistsError:
            await self._reply_t(
                client, message, 'admin.user_exists', user_id=new_user_id
            )
        except Exception as err:
            self._log.exception('Failed to add user')
            await self._reply_t(client, message, 'admin.add_user_failed', error=err)
        else:
            # Ticks rather than Python's True/False, which reads as neither
            # English nor anything else.
            await self._reply_t(
                client,
                message,
                'admin.user_added',
                user_id=new_user_id,
                is_admin=self._tick(user.is_admin),
                media_type=user.download_media_type.value,
                save_to_storage=self._tick(user.save_to_storage),
            )

    async def on_deleteuser(self, client: VideoBotClient, message: Message) -> None:
        """Handle /deleteuser <user_id> command."""
        if await self._refuse_non_admin(client, message):
            return

        parts = message.text.split()
        if len(parts) != 2:
            await self._reply_t(client, message, 'admin.deleteuser_usage')
            return

        try:
            target_user_id = int(parts[1])
        except ValueError:
            await self._reply_t(client, message, 'admin.invalid_user_id')
            return

        try:
            config_manager.delete_user(client, target_user_id)
        except UserNotFoundError:
            await self._reply_t(
                client, message, 'admin.user_not_found', user_id=target_user_id
            )
        except CannotDeleteAdminError:
            await self._reply_t(
                client, message, 'admin.cannot_delete_admin', user_id=target_user_id
            )
        except Exception as err:
            self._log.exception('Failed to delete user')
            await self._reply_t(client, message, 'admin.delete_user_failed', error=err)
        else:
            await self._reply_t(
                client, message, 'admin.user_deleted', user_id=target_user_id
            )

    async def on_config(self, client: VideoBotClient, message: Message) -> None:
        """Handle /config command.

        Usage:
            /config get <path>           - Get config value
            /config set <path> <value>   - Set config value
        """
        if await self._refuse_non_admin(client, message):
            return

        parts = message.text.split(maxsplit=3)
        if len(parts) < 3:
            await self._reply_t(client, message, 'admin.config_usage')
            return

        action = parts[1].lower()
        path = parts[2]

        if action == 'get':
            try:
                value = config_manager.get_config_value(path)
            except Exception as err:
                self._log.exception('Failed to get config value')
                await self._reply_t(
                    client, message, 'admin.config_get_failed', error=err
                )
            else:
                await self._reply_t(
                    client, message, 'admin.config_get_result', path=path, value=value
                )

        elif action == 'set':
            if len(parts) < 4:
                await self._reply_t(client, message, 'admin.config_value_missing')
                return

            try:
                new_value = config_manager.set_config_value(client, path, parts[3])
            except Exception as err:
                self._log.exception('Failed to set config value')
                await self._reply_t(
                    client, message, 'admin.config_set_failed', error=err
                )
            else:
                await self._reply_t(
                    client,
                    message,
                    'admin.config_set_result',
                    path=path,
                    value=new_value,
                )
        else:
            await self._reply_t(
                client, message, 'admin.config_unknown_action', action=action
            )

    async def on_listusers(self, client: VideoBotClient, message: Message) -> None:
        """Handle /listusers command."""
        if await self._refuse_non_admin(client, message):
            return

        language = client.language_for(self._sender_id(message), message.chat.id)
        try:
            users = config_manager.list_users(client)
        except Exception as err:
            self._log.exception('Failed to list users')
            await self._reply(message, t('admin.users_failed', language, error=err))
            return

        if not users:
            await self._reply(message, t('admin.users_none', language))
            return

        lines = [t('admin.users_header', language, count=len(users)), '']
        for user in users:
            lines.append(
                t(
                    'admin.users_row',
                    language,
                    badge='👑' if user['is_admin'] else '👤',
                    user_id=user['id'],
                    media_type=user['download_media_type'],
                    storage=self._tick(user['save_to_storage']),
                )
            )
        await self._reply(message, '\n'.join(lines))

    async def on_reloadconfig(self, client: VideoBotClient, message: Message) -> None:
        """Handle /reloadconfig command."""
        if await self._refuse_non_admin(client, message):
            return

        try:
            config = config_manager.reload_config(client)
        except Exception as err:
            self._log.exception('Failed to reload config')
            await self._reply_t(client, message, 'admin.reload_failed', error=err)
            return

        # Read after the reload: the admin may have just changed their own
        # language, and the confirmation is the first message that should show it.
        await self._reply_t(
            client,
            message,
            'admin.config_reloaded',
            users=len(client.allowed_users),
            admins=len(client.admin_users),
            max_upload_tasks=config.telegram.max_upload_tasks,
        )

    async def on_restartbot(self, client: VideoBotClient, message: Message) -> None:
        """Handle /restartbot command - gracefully restart the bot container."""
        if await self._refuse_non_admin(client, message):
            return

        self._log.info('Bot restart requested by user %d', self._sender_id(message))
        await self._reply_t(client, message, 'admin.restarting')
        sys.exit(0)
