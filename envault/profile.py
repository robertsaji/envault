"""Profile support: named sets of config overrides (e.g. dev, staging, prod)."""
from __future__ import annotations

import copy
from pathlib import Path
from typing import Dict, List

from envault.config import load_config, save_config


class ProfileError(Exception):
    """Raised when a profile operation fails."""


_PROFILES_KEY = "profiles"


def list_profiles(config_path: Path) -> List[str]:
    """Return the names of all defined profiles."""
    cfg = load_config(config_path)
    return sorted(cfg.get(_PROFILES_KEY, {}).keys())


def get_profile(config_path: Path, name: str) -> Dict:
    """Return the overrides stored under *name*.

    Raises ProfileError if the profile does not exist.
    """
    cfg = load_config(config_path)
    profiles = cfg.get(_PROFILES_KEY, {})
    if name not in profiles:
        raise ProfileError(f"Profile '{name}' not found.")
    return dict(profiles[name])


def set_profile(config_path: Path, name: str, overrides: Dict) -> None:
    """Create or replace a profile with *overrides*.

    *overrides* must be a flat mapping of string keys to string values.
    """
    if not name or not name.isidentifier():
        raise ProfileError(
            f"Profile name '{name}' is invalid; use a simple identifier."
        )
    cfg = load_config(config_path)
    profiles = cfg.setdefault(_PROFILES_KEY, {})
    profiles[name] = copy.deepcopy(overrides)
    save_config(config_path, cfg)


def delete_profile(config_path: Path, name: str) -> None:
    """Remove profile *name*.

    Raises ProfileError if it does not exist.
    """
    cfg = load_config(config_path)
    profiles = cfg.get(_PROFILES_KEY, {})
    if name not in profiles:
        raise ProfileError(f"Profile '{name}' not found.")
    del profiles[name]
    save_config(config_path, cfg)


def apply_profile(base_env: Dict[str, str], overrides: Dict) -> Dict[str, str]:
    """Return a new env dict with *overrides* merged on top of *base_env*."""
    merged = dict(base_env)
    merged.update({str(k): str(v) for k, v in overrides.items()})
    return merged
