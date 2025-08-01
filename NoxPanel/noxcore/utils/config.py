import json
import logging
from pathlib import Path
from typing import Any, Dict

logger = logging.getLogger(__name__)


class NoxConfig:
    """Configuration management for NoxPanel with robust error handling and validation."""

    def __init__(self, config_dir: str = "config") -> None:
        """Initialize configuration manager.

        Args:
            config_dir: Directory path for configuration files
        """
        self.config_dir = Path(config_dir)
        self.config_file = self.config_dir / "noxpanel.json"
        self.config: Dict[str, Any] = {}
        self.load_config()

    def load_config(self) -> None:
        """Load configuration from file with error handling."""
        try:
            if self.config_file.exists():
                with open(self.config_file, "r", encoding="utf-8") as f:
                    self.config = json.load(f)
                logger.info(f"Configuration loaded from {self.config_file}")
            else:
                self.config = self.get_default_config()
                self.save_config()
                logger.info("Default configuration created")
        except (json.JSONDecodeError, IOError) as e:
            logger.error(f"Failed to load configuration: {e}")
            self.config = self.get_default_config()

    def save_config(self) -> None:
        """Save configuration to file with error handling."""
        try:
            self.config_dir.mkdir(parents=True, exist_ok=True)
            with open(self.config_file, "w", encoding="utf-8") as f:
                json.dump(self.config, f, indent=2, ensure_ascii=False)
            logger.debug(f"Configuration saved to {self.config_file}")
        except (IOError, OSError) as e:
            logger.error(f"Failed to save configuration: {e}")
            raise

    def get_default_config(self) -> Dict[str, Any]:
        """Get default configuration with comprehensive settings.

        Returns:
            Default configuration dictionary
        """
        return {
            "app": {
                "name": "NoxPanel",
                "version": "1.0.0",
                "debug": False,
                "host": "0.0.0.0",
                "port": 5000,
            },
            "security": {
                "max_script_runtime": 300,
                "allowed_script_extensions": [".py", ".sh"],
                "require_auth": True,
                "session_timeout": 3600,
                "max_login_attempts": 5,
            },
            "logging": {
                "level": "INFO",
                "max_log_size": "10MB",
                "backup_count": 5,
                "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            },
            "database": {
                "type": "sqlite",
                "path": "data/db/noxpanel.db",
                "pool_size": 10,
                "timeout": 30.0,
            },
            "theme": {
                "default": "dark",
                "custom_css": "",
                "available_themes": ["dark", "light", "auto"],
            },
            "plugins": {
                "enabled": True,
                "auto_load": True,
                "paths": ["plugins", "external_plugins"],
            },
        }

    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value using dot notation.

        Args:
            key: Configuration key using dot notation (e.g., 'app.debug')
            default: Default value if key not found

        Returns:
            Configuration value or default
        """
        try:
            keys = key.split(".")
            value = self.config
            for k in keys:
                if isinstance(value, dict) and k in value:
                    value = value[k]
                else:
                    return default
            return value
        except (AttributeError, KeyError, TypeError):
            logger.warning(f"Configuration key '{key}' not found, using default")
            return default

    def set(self, key: str, value: Any) -> None:
        """Set configuration value using dot notation.

        Args:
            key: Configuration key using dot notation (e.g., 'app.debug')
            value: Value to set
        """
        try:
            keys = key.split(".")
            config = self.config
            for k in keys[:-1]:
                config = config.setdefault(k, {})
            config[keys[-1]] = value
            self.save_config()
            logger.debug(f"Configuration key '{key}' set to '{value}'")
        except (AttributeError, KeyError, TypeError) as e:
            logger.error(f"Failed to set configuration key '{key}': {e}")
            raise

    def update(self, new_config: Dict[str, Any]) -> None:
        """Update configuration with new values.

        Args:
            new_config: Dictionary with new configuration values
        """
        try:
            self._deep_update(self.config, new_config)
            self.save_config()
            logger.info("Configuration updated successfully")
        except Exception as e:
            logger.error(f"Failed to update configuration: {e}")
            raise

    def _deep_update(
        self, base_dict: Dict[str, Any], update_dict: Dict[str, Any]
    ) -> None:
        """Recursively update nested dictionaries.

        Args:
            base_dict: Base dictionary to update
            update_dict: Dictionary with updates
        """
        for key, value in update_dict.items():
            if (
                key in base_dict
                and isinstance(base_dict[key], dict)
                and isinstance(value, dict)
            ):
                self._deep_update(base_dict[key], value)
            else:
                base_dict[key] = value

    def validate_config(self) -> bool:
        """Validate configuration integrity.

        Returns:
            True if configuration is valid, False otherwise
        """
        required_sections = ["app", "security", "logging"]

        for section in required_sections:
            if section not in self.config:
                logger.error(f"Missing required configuration section: {section}")
                return False

        # Validate specific settings
        if not isinstance(self.get("app.port"), int) or not (
            1 <= self.get("app.port") <= 65535
        ):
            logger.error("Invalid port configuration")
            return False

        if (
            not isinstance(self.get("security.max_script_runtime"), int)
            or self.get("security.max_script_runtime") <= 0
        ):
            logger.error("Invalid script runtime configuration")
            return False

        logger.debug("Configuration validation passed")
        return True

    def reset_to_defaults(self) -> None:
        """Reset configuration to default values."""
        self.config = self.get_default_config()
        self.save_config()
        logger.info("Configuration reset to defaults")
