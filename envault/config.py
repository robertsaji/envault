"""Configuration management for envault using a .envault.toml file."""

import os
import tomllib
import tomli_w
from typing import Any

DEFAULT_CONFIG_FILE = ".envault.toml"


class ConfigError(Exception):
    """Raised when configuration is invalid or missing."""
    pass


def load_config(config_path: str = DEFAULT_CONFIG_FILE) -> dict[str, Any]:
    """Load envault configuration from a TOML file.

    Args:
        config_path: Path to the configuration file.

    Returns:
        Parsed configuration dictionary.

    Raises:
        ConfigError: If the file is missing or malformed.
    """
    if not os.path.exists(config_path):
        raise ConfigError(
            f"Configuration file '{config_path}' not found. "
            "Run 'envault init' to create one."
        )
    try:
        with open(config_path, "rb") as f:
            return tomllib.load(f)
    except tomllib.TOMLDecodeError as e:
        raise ConfigError(f"Invalid TOML in '{config_path}': {e}") from e


def save_config(config: dict[str, Any], config_path: str = DEFAULT_CONFIG_FILE) -> None:
    """Save envault configuration to a TOML file.

    Args:
        config: Configuration dictionary to persist.
        config_path: Path to the configuration file.
    """
    with open(config_path, "wb") as f:
        tomli_w.dump(config, f)


def init_config(env_file: str = ".env", recipients: list[str] | None = None) -> dict[str, Any]:
    """Create a default configuration dictionary.

    Args:
        env_file: Path to the .env file to encrypt.
        recipients: List of GPG key IDs or emails.

    Returns:
        Default configuration dictionary.
    """
    return {
        "envault": {
            "env_file": env_file,
            "encrypted_file": env_file + ".gpg",
        },
        "recipients": recipients or [],
    }


def get_recipients(config: dict[str, Any]) -> list[str]:
    """Extract recipient list from config, raising if empty."""
    recipients = config.get("recipients", [])
    if not recipients:
        raise ConfigError(
            "No recipients configured. Add GPG key IDs to '.envault.toml' under [recipients]."
        )
    return recipients
