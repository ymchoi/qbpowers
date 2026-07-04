"""utils/fetch_web internal constants."""

from pathlib import Path

# Persistent Patchright Chrome profile shared by fetch_site and launch_chrome.
# Hardcoded so callers don't need to manage profile paths.
_PROFILE_DIR: Path = Path.home() / "Documents" / "patchright_profile"
