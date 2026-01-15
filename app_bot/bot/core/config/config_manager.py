"""Configuration manager for hot-reload and dynamic config updates."""

import logging
import shutil
from collections.abc import Mapping, Sequence
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING, Any

from pydantic import ValidationError
from ruamel.yaml import YAML
from ruamel.yaml.comments import CommentedMap, CommentedSeq
from ruamel.yaml.scalarstring import ScalarString
from ruamel.yaml.scalarbool import ScalarBoolean
from ruamel.yaml.scalarint import ScalarInt
from ruamel.yaml.scalarfloat import ScalarFloat

from bot.core.schemas import ConfigSchema, UploadSchema, UserSchema, VideoCaptionSchema

if TYPE_CHECKING:
    from bot.bot.client import VideoBotClient


class ConfigManager:
    """Manages configuration file operations with hot-reload support."""

    _CONF_FILENAME = 'config.yml'
    _BACKUP_DIR = 'config_backups'

    def __init__(self) -> None:
        self._log = logging.getLogger(self.__class__.__name__)
        self._yaml = YAML()
        self._yaml.preserve_quotes = True
        self._yaml.indent(mapping=2, sequence=4, offset=2)

        self._config_dir = Path(__file__).parent.parent.parent.parent
        self._config_path = self._config_dir / self._CONF_FILENAME
        self._backup_dir = self._config_dir / self._BACKUP_DIR

    def _create_backup(self) -> Path | None:
        """Create backup of current config before modifications."""
        if not self._config_path.exists():
            return None

        self._backup_dir.mkdir(exist_ok=True)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_path = self._backup_dir / f'config_{timestamp}.yml'
        shutil.copy2(self._config_path, backup_path)
        self._log.info('Created config backup: %s', backup_path)

        self._cleanup_old_backups(keep=5)
        return backup_path

    def _cleanup_old_backups(self, keep: int = 5) -> None:
        """Remove old backups, keeping only the most recent ones."""
        backups = sorted(self._backup_dir.glob('config_*.yml'), reverse=True)
        for backup in backups[keep:]:
            backup.unlink()
            self._log.debug('Removed old backup: %s', backup)

    def _load_raw_config(self) -> dict:
        """Load raw YAML config preserving structure."""
        with self._config_path.open() as f:
            return self._yaml.load(f)

    def _save_raw_config(self, data: dict) -> None:
        """Save config directly to file.

        Note: Writing directly instead of atomic temp+move because
        Docker bind mounts don't support cross-filesystem operations reliably.
        """
        self._log.info('Saving config to: %s (exists: %s)', self._config_path, self._config_path.exists())
        try:
            with self._config_path.open('w') as f:
                self._yaml.dump(data, f)
                f.flush()
                import os
                os.fsync(f.fileno())
            self._log.info('Config saved successfully to %s', self._config_path)
        except Exception as e:
            self._log.error('Failed to save config: %s', e)
            raise

    def _to_plain_python(self, obj: Any) -> Any:
        """Convert ruamel.yaml objects to plain Python types for Pydantic."""
        if isinstance(obj, CommentedMap):
            return {k: self._to_plain_python(v) for k, v in obj.items()}
        elif isinstance(obj, CommentedSeq):
            return [self._to_plain_python(item) for item in obj]
        elif isinstance(obj, ScalarBoolean):
            return bool(obj)
        elif isinstance(obj, ScalarInt):
            return int(obj)
        elif isinstance(obj, ScalarFloat):
            return float(obj)
        elif isinstance(obj, ScalarString):
            return str(obj)
        elif hasattr(obj, 'value'):
            # Handle TaggedScalar and other tagged values
            return obj.value
        elif isinstance(obj, Mapping):
            return {k: self._to_plain_python(v) for k, v in obj.items()}
        elif isinstance(obj, Sequence) and not isinstance(obj, str):
            return [self._to_plain_python(item) for item in obj]
        return obj

    def _validate_config(self, data: dict) -> ConfigSchema:
        """Validate config data against schema."""
        plain_data = self._to_plain_python(data)
        return ConfigSchema(**plain_data)

    def reload_config(self, bot: 'VideoBotClient') -> ConfigSchema:
        """Reload config from file and update bot's in-memory state."""
        self._log.info('Reloading configuration from file')

        raw_config = self._load_raw_config()
        new_config = self._validate_config(raw_config)

        # Update bot's config reference
        bot.conf = new_config

        # Rebuild user dictionaries
        bot.allowed_users.clear()
        bot.admin_users.clear()

        for user in new_config.telegram.allowed_users:
            bot.allowed_users[user.id] = user
            if user.is_admin:
                bot.admin_users[user.id] = user

        self._log.info(
            'Config reloaded: %d users (%d admins)',
            len(bot.allowed_users),
            len(bot.admin_users),
        )
        return new_config

    def add_user(self, bot: 'VideoBotClient', user_id: int) -> UserSchema:
        """Add a new user with default settings."""
        self._log.info('Adding user: %d', user_id)

        # Check if user already exists
        if user_id in bot.allowed_users:
            raise ValueError(f'User {user_id} already exists')

        self._create_backup()
        raw_config = self._load_raw_config()

        # Create default user config
        new_user_data = {
            'id': user_id,
            'is_admin': False,
            'send_startup_message': False,
            'download_media_type': 'VIDEO',
            'save_to_storage': False,
            'use_url_regex_match': True,
            'save_to_database': True,
            'upload': {
                'upload_video_file': True,
                'upload_video_max_file_size': 2147483648,
                'forward_to_group': False,
                'forward_group_id': None,
                'silent': False,
                'video_caption': {
                    'include_title': True,
                    'include_filename': False,
                    'include_link': True,
                    'include_size': False,
                },
            },
        }

        raw_config['telegram']['allowed_users'].append(new_user_data)

        # Validate before saving
        self._validate_config(raw_config)
        self._save_raw_config(raw_config)

        # Reload to apply changes
        self.reload_config(bot)

        return bot.allowed_users[user_id]

    def delete_user(self, bot: 'VideoBotClient', user_id: int) -> None:
        """Delete a user from config."""
        self._log.info('Deleting user: %d', user_id)

        # Check if user exists
        if user_id not in bot.allowed_users:
            raise ValueError(f'User {user_id} not found')

        # Prevent deleting admins
        if user_id in bot.admin_users:
            raise ValueError(f'Cannot delete admin user {user_id}. Edit config file manually.')

        self._create_backup()
        raw_config = self._load_raw_config()

        # Remove user from list
        raw_config['telegram']['allowed_users'] = [
            u for u in raw_config['telegram']['allowed_users']
            if u['id'] != user_id
        ]

        # Validate before saving
        self._validate_config(raw_config)
        self._save_raw_config(raw_config)

        # Reload to apply changes
        self.reload_config(bot)

    def get_config_value(self, path: str) -> Any:
        """Get config value by dot-separated path (e.g., 'telegram.max_upload_tasks')."""
        raw_config = self._load_raw_config()

        keys = path.split('.')
        value = raw_config
        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                raise KeyError(f'Config path not found: {path}')

        return value

    def set_config_value(self, bot: 'VideoBotClient', path: str, value: str) -> Any:
        """Set config value by dot-separated path."""
        self._log.info('Setting config: %s = %s', path, value)

        self._create_backup()
        raw_config = self._load_raw_config()

        keys = path.split('.')
        target = raw_config

        # Navigate to parent of the target key
        for key in keys[:-1]:
            if isinstance(target, dict) and key in target:
                target = target[key]
            else:
                raise KeyError(f'Config path not found: {path}')

        last_key = keys[-1]
        if last_key not in target:
            raise KeyError(f'Config path not found: {path}')

        # Convert value to appropriate type based on old value
        old_value = target[last_key]
        new_value = self._convert_value(value, old_value)

        target[last_key] = new_value

        # Validate before saving
        self._validate_config(raw_config)
        self._save_raw_config(raw_config)

        # Reload to apply changes
        self.reload_config(bot)

        return new_value

    def _convert_value(self, value: str, old_value: Any) -> Any:
        """Convert string value to appropriate type based on old value."""
        # Get plain Python value to determine type
        plain_old = self._to_plain_python(old_value)
        target_type = type(plain_old)

        if target_type == bool:
            return value.lower() in ('true', '1', 'yes', 'on')
        elif target_type == int:
            return int(value)
        elif target_type == float:
            return float(value)
        elif target_type == str:
            return value
        else:
            # For complex types, return as string
            return value

    def list_users(self, bot: 'VideoBotClient') -> list[dict]:
        """Get list of all users with their basic info."""
        users = []
        for user in bot.allowed_users.values():
            users.append({
                'id': user.id,
                'is_admin': user.is_admin,
                'download_media_type': str(user.download_media_type.value),
                'save_to_storage': user.save_to_storage,
            })
        return users


# Singleton instance
config_manager = ConfigManager()
