"""Admin command handlers for bot configuration management."""

import logging

from pyrogram.enums import ParseMode
from pyrogram.types import Message

from bot.bot.client import VideoBotClient
from bot.core.config.config_manager import config_manager
from bot.core.utils import bold


class AdminCommandHandler:
    """Handles admin commands for bot configuration."""

    def __init__(self) -> None:
        self._log = logging.getLogger(self.__class__.__name__)

    def _is_admin(self, bot: VideoBotClient, user_id: int) -> bool:
        """Check if user is an admin."""
        return user_id in bot.admin_users

    async def _reply(self, message: Message, text: str) -> None:
        """Send reply with HTML formatting."""
        await message.reply(
            text=text,
            parse_mode=ParseMode.HTML,
            reply_to_message_id=message.id,
        )

    async def on_adduser(self, client: VideoBotClient, message: Message) -> None:
        """Handle /adduser <user_id> command."""
        user_id = message.from_user.id if message.from_user else message.chat.id

        if not self._is_admin(client, user_id):
            await self._reply(message, '🚫 This command is only for admins.')
            return

        parts = message.text.split()
        if len(parts) != 2:
            await self._reply(
                message,
                f'❌ Usage: {bold("/adduser <telegram_id>")}\n'
                f'Example: /adduser 123456789'
            )
            return

        try:
            new_user_id = int(parts[1])
        except ValueError:
            await self._reply(message, '❌ Invalid user ID. Must be a number.')
            return

        try:
            user = config_manager.add_user(client, new_user_id)
            await self._reply(
                message,
                f'✅ User {bold(str(new_user_id))} added successfully!\n\n'
                f'Settings:\n'
                f'• Admin: {user.is_admin}\n'
                f'• Media type: {user.download_media_type.value}\n'
                f'• Save to storage: {user.save_to_storage}\n\n'
                f'💡 Config file updated and reloaded.'
            )
        except ValueError as e:
            await self._reply(message, f'❌ {e}')
        except Exception as e:
            self._log.exception('Failed to add user')
            await self._reply(message, f'❌ Failed to add user: {e}')

    async def on_deleteuser(self, client: VideoBotClient, message: Message) -> None:
        """Handle /deleteuser <user_id> command."""
        user_id = message.from_user.id if message.from_user else message.chat.id

        if not self._is_admin(client, user_id):
            await self._reply(message, '🚫 This command is only for admins.')
            return

        parts = message.text.split()
        if len(parts) != 2:
            await self._reply(
                message,
                f'❌ Usage: {bold("/deleteuser <telegram_id>")}\n'
                f'Example: /deleteuser 123456789'
            )
            return

        try:
            target_user_id = int(parts[1])
        except ValueError:
            await self._reply(message, '❌ Invalid user ID. Must be a number.')
            return

        try:
            config_manager.delete_user(client, target_user_id)
            await self._reply(
                message,
                f'✅ User {bold(str(target_user_id))} deleted successfully!\n\n'
                f'💡 Config file updated and reloaded.'
            )
        except ValueError as e:
            await self._reply(message, f'❌ {e}')
        except Exception as e:
            self._log.exception('Failed to delete user')
            await self._reply(message, f'❌ Failed to delete user: {e}')

    async def on_config(self, client: VideoBotClient, message: Message) -> None:
        """Handle /config command.

        Usage:
            /config get <path>           - Get config value
            /config set <path> <value>   - Set config value
        """
        user_id = message.from_user.id if message.from_user else message.chat.id

        if not self._is_admin(client, user_id):
            await self._reply(message, '🚫 This command is only for admins.')
            return

        parts = message.text.split(maxsplit=3)
        if len(parts) < 3:
            await self._reply(
                message,
                f'❌ Usage:\n'
                f'{bold("/config get <path>")} - Get config value\n'
                f'{bold("/config set <path> <value>")} - Set config value\n\n'
                f'Examples:\n'
                f'/config get telegram.max_upload_tasks\n'
                f'/config set telegram.max_upload_tasks 10'
            )
            return

        action = parts[1].lower()
        path = parts[2]

        if action == 'get':
            try:
                value = config_manager.get_config_value(path)
                await self._reply(
                    message,
                    f'📋 {bold(path)} = {value}'
                )
            except KeyError as e:
                await self._reply(message, f'❌ {e}')
            except Exception as e:
                self._log.exception('Failed to get config value')
                await self._reply(message, f'❌ Failed to get value: {e}')

        elif action == 'set':
            if len(parts) < 4:
                await self._reply(
                    message,
                    f'❌ Missing value. Usage: {bold("/config set <path> <value>")}'
                )
                return

            value = parts[3]
            try:
                new_value = config_manager.set_config_value(client, path, value)
                await self._reply(
                    message,
                    f'✅ Config updated!\n'
                    f'{bold(path)} = {new_value}\n\n'
                    f'💡 Config file updated and reloaded.'
                )
            except KeyError as e:
                await self._reply(message, f'❌ {e}')
            except Exception as e:
                self._log.exception('Failed to set config value')
                await self._reply(message, f'❌ Failed to set value: {e}')
        else:
            await self._reply(
                message,
                f'❌ Unknown action: {action}\n'
                f'Use {bold("get")} or {bold("set")}'
            )

    async def on_listusers(self, client: VideoBotClient, message: Message) -> None:
        """Handle /listusers command."""
        user_id = message.from_user.id if message.from_user else message.chat.id

        if not self._is_admin(client, user_id):
            await self._reply(message, '🚫 This command is only for admins.')
            return

        try:
            users = config_manager.list_users(client)

            if not users:
                await self._reply(message, '📋 No users configured.')
                return

            lines = [f'📋 {bold("Configured Users")} ({len(users)})\n']
            for u in users:
                admin_badge = '👑' if u['is_admin'] else '👤'
                lines.append(
                    f'{admin_badge} {bold(str(u["id"]))}\n'
                    f'   Media: {u["download_media_type"]} | '
                    f'Storage: {"✅" if u["save_to_storage"] else "❌"}'
                )

            await self._reply(message, '\n'.join(lines))
        except Exception as e:
            self._log.exception('Failed to list users')
            await self._reply(message, f'❌ Failed to list users: {e}')

    async def on_reloadconfig(self, client: VideoBotClient, message: Message) -> None:
        """Handle /reloadconfig command."""
        user_id = message.from_user.id if message.from_user else message.chat.id

        if not self._is_admin(client, user_id):
            await self._reply(message, '🚫 This command is only for admins.')
            return

        try:
            config = config_manager.reload_config(client)
            await self._reply(
                message,
                f'✅ Config reloaded successfully!\n\n'
                f'• Users: {len(client.allowed_users)}\n'
                f'• Admins: {len(client.admin_users)}\n'
                f'• Max upload tasks: {config.telegram.max_upload_tasks}'
            )
        except Exception as e:
            self._log.exception('Failed to reload config')
            await self._reply(message, f'❌ Failed to reload config: {e}')
