"""Open a patchright Chrome window for manual interaction.

The window navigates to <url> and stays open until the user closes all
browser windows. Cookies and session state persist in a fixed profile
directory (~/Documents/patchright_profile), so re-running preserves logins.

Usage:
    python launch_chrome.py <url>
"""

import argparse
import asyncio
import sys
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path

from patchright.async_api import Error as PatchrightError
from patchright.async_api import async_playwright

try:
    from fetch_web import _PROFILE_DIR
except ImportError:
    # Direct execution: make the fetch_web package importable.
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
    from fetch_web import _PROFILE_DIR


@dataclass(frozen=True, slots=True)
class LaunchCliArgs:
    url: str


def _required_str(value: object, name: str) -> str:
    if not isinstance(value, str):
        raise TypeError(f"expected argparse field {name!r} to be str")
    return value


def parse_args(argv: Sequence[str] | None = None) -> LaunchCliArgs:
    parser = argparse.ArgumentParser(
        description="Open a patchright Chrome window for manual interaction."
    )
    parser.add_argument("url", help="Initial URL to navigate to.")
    namespace = parser.parse_args(argv)
    raw_url: object = namespace.url
    return LaunchCliArgs(url=_required_str(raw_url, "url"))


async def launch(url: str) -> int:
    _PROFILE_DIR.mkdir(parents=True, exist_ok=True)
    print(f"[patchright] profile dir: {_PROFILE_DIR}", flush=True)

    async with async_playwright() as p:
        ctx = await p.chromium.launch_persistent_context(
            user_data_dir=str(_PROFILE_DIR),
            channel="chrome",
            headless=False,
            no_viewport=True,
        )
        page = ctx.pages[0] if ctx.pages else await ctx.new_page()
        try:
            await page.goto(url)
        except PatchrightError as e:
            print(
                f"[patchright] initial goto failed ({type(e).__name__}: {e}); window stays open.",
                flush=True,
            )
        print(
            f"[patchright] window opened at {url}. Close all browser windows to exit.",
            flush=True,
        )

        closed = asyncio.Event()

        def mark_closed(*_: object) -> None:
            closed.set()

        ctx.on("close", mark_closed)
        try:
            await closed.wait()
        except KeyboardInterrupt:
            pass
        finally:
            print("[patchright] context closed. exiting.", flush=True)
    return 0


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    return asyncio.run(launch(args.url))


if __name__ == "__main__":
    sys.exit(main())
