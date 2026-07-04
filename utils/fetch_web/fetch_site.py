"""Capture a web page (HTML + full-page screenshot) using patchright Chrome.

Usage:
    python fetch_site.py <url> <store>

- <url>: page URL to fetch.
- <store>: directory where page.html, page.png, meta.json, run.log are written
           (created if missing; existing files are overwritten).

The Patchright Chrome profile is fixed to ~/Documents/patchright_profile
(persistent across runs). The browser always runs in headed mode because
Patchright loses bot-detection evasion when run headless.
"""

import argparse
import asyncio
import json
import shutil
import sys
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import TypedDict

from patchright.async_api import BrowserContext, async_playwright
from patchright.async_api import TimeoutError as PatchrightTimeoutError

try:
    from fetch_web import _PROFILE_DIR
except ImportError:
    # Direct execution: make the fetch_web package importable.
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
    from fetch_web import _PROFILE_DIR


@dataclass(frozen=True, slots=True)
class FetchCliArgs:
    url: str
    store: Path


class CaptureMeta(TypedDict):
    saved_at: str
    input_url: str
    final_url: str
    page_title: str
    profile_dir: str
    store_dir: str
    html_chars: int
    html_file: str
    screenshot_file: str


def _required_str(value: object, name: str) -> str:
    if not isinstance(value, str):
        raise TypeError(f"expected argparse field {name!r} to be str")
    return value


def _required_path(value: object, name: str) -> Path:
    if not isinstance(value, Path):
        raise TypeError(f"expected argparse field {name!r} to be Path")
    return value


def parse_args(argv: Sequence[str] | None = None) -> FetchCliArgs:
    parser = argparse.ArgumentParser(
        description="Capture a web page (HTML + full-page screenshot) using patchright Chrome."
    )
    parser.add_argument("url", help="Page URL to fetch.")
    parser.add_argument(
        "store",
        type=Path,
        help="Output directory for page.html, page.png, meta.json, run.log.",
    )
    namespace = parser.parse_args(argv)
    raw_url: object = namespace.url
    raw_store: object = namespace.store
    return FetchCliArgs(
        url=_required_str(raw_url, "url"),
        store=_required_path(raw_store, "store"),
    )


def _clear_directory_contents(directory: Path) -> None:
    for child in directory.iterdir():
        if child.is_dir() and not child.is_symlink():
            shutil.rmtree(child)
        else:
            child.unlink()


async def fetch(url: str, store: Path) -> int:
    _PROFILE_DIR.mkdir(parents=True, exist_ok=True)
    store.mkdir(parents=True, exist_ok=True)
    # Clear existing contents of <store> before writing fresh outputs.
    _clear_directory_contents(store)

    log: list[str] = []

    def step(msg: str) -> None:
        line = f"[{datetime.now().strftime('%H:%M:%S')}] {msg}"
        print(line, flush=True)
        log.append(line)

    ctx: BrowserContext | None = None
    completed = False
    close_error: BaseException | None = None
    try:
        async with async_playwright() as p:
            try:
                ctx = await p.chromium.launch_persistent_context(
                    user_data_dir=str(_PROFILE_DIR),
                    channel="chrome",
                    headless=False,
                    no_viewport=True,
                )
                page = ctx.pages[0] if ctx.pages else await ctx.new_page()

                step(f"goto {url}")
                await page.goto(url, wait_until="domcontentloaded", timeout=45000)
                try:
                    await page.wait_for_load_state("networkidle", timeout=20000)
                except PatchrightTimeoutError:
                    step("networkidle wait skipped: TimeoutError")

                step("scrolling to trigger lazy-load sections")
                prev_height = await page.evaluate("() => document.body.scrollHeight")
                for _ in range(20):
                    await page.evaluate("() => window.scrollBy(0, window.innerHeight)")
                    await page.wait_for_timeout(350)
                    new_height = await page.evaluate("() => document.body.scrollHeight")
                    if new_height == prev_height:
                        break
                    prev_height = new_height
                await page.evaluate("() => window.scrollTo(0, 0)")
                await page.wait_for_timeout(600)

                page_url = page.url
                page_title = await page.title()
                step(f"final url: {page_url}")
                step(f"title: {page_title}")

                html = await page.content()
                html_path = store / "page.html"
                html_path.write_text(html, encoding="utf-8")
                step(f"saved HTML: {html_path.name} ({len(html)} chars)")

                screenshot_path = store / "page.png"
                await page.screenshot(path=str(screenshot_path), full_page=True)
                size = screenshot_path.stat().st_size if screenshot_path.exists() else 0
                step(f"saved screenshot: {screenshot_path.name} ({size} bytes)")

                meta: CaptureMeta = {
                    "saved_at": datetime.now().isoformat(),
                    "input_url": url,
                    "final_url": page_url,
                    "page_title": page_title,
                    "profile_dir": str(_PROFILE_DIR),
                    "store_dir": str(store),
                    "html_chars": len(html),
                    "html_file": "page.html",
                    "screenshot_file": "page.png",
                }
                meta_path = store / "meta.json"
                meta_path.write_text(json.dumps(meta, indent=2, ensure_ascii=False), encoding="utf-8")
                step(f"saved meta: {meta_path.name}")
                completed = True
            finally:
                active_error = sys.exception()
                if ctx is not None:
                    try:
                        await ctx.close()
                    except BaseException as e:
                        close_error = e
                        step(f"context close failed: {type(e).__name__}: {e}")
                        if active_error is None:
                            raise
                if completed and close_error is None:
                    step("done")
    except BaseException as e:
        step(f"failed: {type(e).__name__}: {e}")
        raise
    finally:
        (store / "run.log").write_text("\n".join(log), encoding="utf-8")
    return 0


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    return asyncio.run(fetch(args.url, args.store))


if __name__ == "__main__":
    sys.exit(main())
